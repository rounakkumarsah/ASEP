from __future__ import annotations

import os
import re

from src.documents.metadata import ChunkRecord, DocumentMetadata, compute_hash


# Markdown-aware separators: keep code blocks, headings, paragraphs together
MARKDOWN_SEPARATORS: list[str] = [
    "\n```",
    "\n## ",
    "\n### ",
    "\n#### ",
    "\n\n",
    "\n",
    ". ",
    "? ",
    "! ",
    " ",
    "",
]

# Code-aware separators: keep class and function definitions together
CODE_SEPARATORS: list[str] = [
    "\nclass ",
    "\ndef ",
    "\nasync def ",
    "\nfunction ",
    "\nexport ",
    "\n\n",
    "\n",
    ";",
    " ",
    "",
]

# General text/prose separators: paragraph -> line -> sentence -> clause -> word -> char
TEXT_SEPARATORS: list[str] = [
    "\n\n",
    "\n",
    ". ",
    "? ",
    "! ",
    "; ",
    ", ",
    " ",
    "",
]

MARKDOWN_EXTENSIONS: set[str] = {".md", ".markdown", ".mdown", ".mkd"}
CODE_EXTENSIONS: set[str] = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".cpp", ".c",
    ".h", ".hpp", ".cs", ".go", ".rs", ".rb", ".php", ".swift",
    ".kt", ".scala", ".sh", ".bash", ".sql", ".yaml", ".yml", ".json",
}


class RecursiveCharacterTextSplitter:
    """Recursively splits text using a priority-ordered list of separators."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: list[str] | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or TEXT_SEPARATORS

    def split_text(self, text: str, custom_separators: list[str] | None = None) -> list[str]:
        """Split text into chunks of chunk_size with overlap."""
        seps = custom_separators or self.separators
        return self._split_text(text, seps)

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        """Recursive helper to split the text."""
        final_chunks: list[str] = []

        # Select the separator
        separator = separators[-1]
        new_separators = []
        for i, s in enumerate(separators):
            escaped_s = re.escape(s) if s != "" else ""
            if s == "":
                new_separators = separators[i + 1:]
                separator = s
                break
            if re.search(escaped_s, text):
                new_separators = separators[i + 1:]
                separator = s
                break

        splits = text.split(separator) if separator != "" else list(text)

        current_doc: list[str] = []
        total_len = 0

        for d in splits:
            d_len = len(d)
            if total_len + d_len + (len(separator) if current_doc else 0) > self.chunk_size:
                if total_len > 0:
                    joined = separator.join(current_doc)
                    if joined:
                        final_chunks.append(joined)
                    while total_len > self.chunk_overlap and current_doc:
                        removed = current_doc.pop(0)
                        total_len -= (len(removed) + len(separator))

                if d_len > self.chunk_size:
                    sub_chunks = self._split_text(d, new_separators)
                    final_chunks.extend(sub_chunks)
                else:
                    current_doc.append(d)
                    total_len += d_len + (len(separator) if len(current_doc) > 1 else 0)
            else:
                current_doc.append(d)
                total_len += d_len + (len(separator) if len(current_doc) > 1 else 0)

        if current_doc:
            joined = separator.join(current_doc)
            if joined:
                final_chunks.append(joined)

        return final_chunks


class ChunkingEngine:
    """Production chunking engine generating hierarchical parent-child relationships with stable IDs.
    
    Supports:
    - Semantic boundary splitting (Markdown, Code, Prose)
    - Heading and section extraction stored in DocumentMetadata.section
    - Filtering of whitespace-only chunks
    - Stable content hashing and parent-child tracking
    """

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        separators: list[str] | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.default_separators = separators
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
        )

    def _detect_separators(self, filename: str, content: str) -> list[str]:
        """Detect the optimal separator list based on file extension and content cues."""
        if self.default_separators:
            return self.default_separators

        _, ext = os.path.splitext(filename.lower())
        if ext in MARKDOWN_EXTENSIONS:
            return MARKDOWN_SEPARATORS
        if ext in CODE_EXTENSIONS:
            return CODE_SEPARATORS

        # Content-based heuristic
        if "\n## " in content or "\n# " in content or "```" in content:
            return MARKDOWN_SEPARATORS
        if re.search(r"\n(?:def |class |async def |function |const )", content):
            return CODE_SEPARATORS

        return TEXT_SEPARATORS

    def _extract_section_for_chunk(self, content: str, chunk_text: str, search_start: int) -> tuple[str | None, int]:
        """Extract the active section/heading preceding the chunk text in the original content."""
        idx = content.find(chunk_text[:min(60, len(chunk_text))], search_start)
        if idx == -1:
            idx = content.find(chunk_text[:min(30, len(chunk_text))])
        next_search_pos = idx + len(chunk_text) if idx != -1 else search_start

        if idx <= 0:
            # Check if chunk itself starts with a heading
            header_match = re.match(r"^(#{1,6}\s+[^\n]+)", chunk_text.strip())
            if header_match:
                section = re.sub(r"^#{1,6}\s*", "", header_match.group(1)).strip()
                return section, next_search_pos
            return None, next_search_pos

        prefix = content[:idx]
        # Look backwards for the most recent markdown heading
        headings = list(re.finditer(r"(?:^|\n)(#{1,6}\s+[^\n]+)", prefix))
        if headings:
            last_heading = headings[-1].group(1)
            section = re.sub(r"^#{1,6}\s*", "", last_heading).strip()
            return section, next_search_pos

        return None, next_search_pos

    def chunk_document(
        self,
        document_id: str,
        content: str,
        filename: str,
        file_path: str,
        collection: str = "default",
        source: str = "local",
        tags: list[str] | None = None,
        separators: list[str] | None = None,
    ) -> list[ChunkRecord]:
        """
        Split a document recursively, assign parent-child linkages,
        extract active section headers, and generate stable IDs using content hashing.
        """
        seps = separators or self._detect_separators(filename, content)
        raw_chunks = self.splitter.split_text(content, custom_separators=seps)

        # Filter whitespace-only chunks
        clean_chunks = [c.strip() for c in raw_chunks if c and c.strip()]
        if not clean_chunks and content.strip():
            clean_chunks = [content.strip()]

        records: list[ChunkRecord] = []
        parent_id = compute_hash(document_id + file_path)

        search_pos = 0
        for idx, text in enumerate(clean_chunks):
            chunk_hash = compute_hash(text)
            chunk_id = compute_hash(f"{file_path}_{idx}_{chunk_hash}")

            section, search_pos = self._extract_section_for_chunk(content, text, search_pos)

            meta = DocumentMetadata(
                document_id=document_id,
                collection=collection,
                source=source,
                filename=filename,
                file_path=file_path,
                section=section,
                chunk_number=idx,
                tags=tags or [],
            )

            records.append(
                ChunkRecord(
                    chunk_id=chunk_id,
                    parent_id=parent_id,
                    content=text,
                    metadata=meta,
                    content_hash=chunk_hash,
                )
            )

        return records
