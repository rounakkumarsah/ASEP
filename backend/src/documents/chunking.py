"""
ASEP — Configurable Recursive Character Text Chunker
"""

import re
from typing import list


class RecursiveCharacterTextSplitter:
    """Recursively splits text using a list of separators."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: list[str] | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> list[str]:
        """Split text into chunks of chunk_size with overlap."""
        return self._split_text(text, self.separators)

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        """Recursive helper to split the text."""
        final_chunks: list[str] = []
        
        # Select the separator
        separator = separators[-1]
        new_separators = []
        for i, s in enumerate(separators):
            # Escape for regex if not empty
            escaped_s = re.escape(s) if s != "" else ""
            if s == "":
                new_separators = separators[i+1:]
                separator = s
                break
            if re.search(escaped_s, text):
                new_separators = separators[i+1:]
                separator = s
                break
        
        # Split by separator
        splits = []
        if separator != "":
            splits = text.split(separator)
        else:
            splits = list(text)

        # Merge splits into chunks
        current_doc: list[str] = []
        total_len = 0
        
        for d in splits:
            d_len = len(d)
            if total_len + d_len + (len(separator) if current_doc else 0) > self.chunk_size:
                if total_len > 0:
                    joined = separator.join(current_doc)
                    if joined:
                        final_chunks.append(joined)
                    # Handle overlap
                    while total_len > self.chunk_overlap and current_doc:
                        removed = current_doc.pop(0)
                        total_len -= (len(removed) + len(separator))
                
                # If a single split is larger than chunk_size, recurse
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
