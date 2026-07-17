from __future__ import annotations
import re
from typing import List, Dict, Any, Optional
from src.documents.metadata import DocumentMetadata, ChunkRecord, compute_hash

class RecursiveCharacterTextSplitter:
    """Recursively splits text using a list of separators."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> List[str]:
        """Split text into chunks of chunk_size with overlap."""
        return self._split_text(text, self.separators)

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Recursive helper to split the text."""
        final_chunks: List[str] = []
        
        # Select the separator
        separator = separators[-1]
        new_separators = []
        for i, s in enumerate(separators):
            escaped_s = re.escape(s) if s != "" else ""
            if s == "":
                new_separators = separators[i+1:]
                separator = s
                break
            if re.search(escaped_s, text):
                new_separators = separators[i+1:]
                separator = s
                break
        
        splits = []
        if separator != "":
            splits = text.split(separator)
        else:
            splits = list(text)

        current_doc: List[str] = []
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
    """Production chunking engine generating hierarchical parent-child relationships with stable IDs."""
    
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150) -> None:
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def chunk_document(
        self,
        document_id: str,
        content: str,
        filename: str,
        file_path: str,
        collection: str = "default",
        source: str = "local",
        tags: List[str] | None = None
    ) -> List[ChunkRecord]:
        """
        Split a document recursively, assign parent-child linkages,
        and generate stable IDs using content hashing.
        """
        raw_chunks = self.splitter.split_text(content)
        records = []
        
        # Parent ID is a stable hash of the entire document
        parent_id = compute_hash(document_id + file_path)
        
        for idx, text in enumerate(raw_chunks):
            # Stable chunk ID based on path + index + content hash
            chunk_hash = compute_hash(text)
            chunk_id = compute_hash(f"{file_path}_{idx}_{chunk_hash}")
            
            meta = DocumentMetadata(
                document_id=document_id,
                collection=collection,
                source=source,
                filename=filename,
                file_path=file_path,
                chunk_number=idx,
                tags=tags or [],
            )
            
            records.append(
                ChunkRecord(
                    chunk_id=chunk_id,
                    parent_id=parent_id,
                    content=text,
                    metadata=meta,
                    content_hash=chunk_hash
                )
            )
            
        return records
