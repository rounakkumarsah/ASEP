"""
ASEP — Native Document Loaders
"""

import os
from abc import ABC, abstractmethod
from typing import Any

import fitz  # PyMuPDF
import docx

class BaseLoader(ABC):
    """Abstract base class for document loaders."""

    @abstractmethod
    def load(self, file_path: str) -> str:
        """Parse file content and return it as raw text."""
        pass


class PDFLoader(BaseLoader):
    """Native PDF Loader using PyMuPDF."""

    def load(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        text_parts = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text_parts.append(page.get_text())
        return "\n".join(text_parts)


class DOCXLoader(BaseLoader):
    """Native DOCX Loader using python-docx."""

    def load(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        doc = docx.Document(file_path)
        text_parts = [p.text for p in doc.paragraphs]
        return "\n".join(text_parts)


class TextLoader(BaseLoader):
    """Loader for Plain Text and Markdown files."""

    def load(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()


def get_loader_for_file(file_path: str) -> BaseLoader:
    """Factory to get the appropriate loader based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return PDFLoader()
    elif ext == ".docx":
        return DOCXLoader()
    elif ext in (".txt", ".md", ".markdown"):
        return TextLoader()
    else:
        # Fallback to TextLoader
        return TextLoader()
