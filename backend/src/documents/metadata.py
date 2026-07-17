from __future__ import annotations
import os
import hashlib
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    document_id: str
    collection: str = "default"
    source: str = "local"
    filename: str
    file_path: str
    section: Optional[str] = None
    page: Optional[int] = None
    chunk_number: int = 0
    created_time: float = Field(default_factory=time.time)
    updated_time: float = Field(default_factory=time.time)
    tags: List[str] = Field(default_factory=list)
    version: str = "1.0"
    permissions: List[str] = Field(default_factory=list)  # Scaffold only

class ChunkRecord(BaseModel):
    chunk_id: str
    parent_id: Optional[str] = None
    content: str
    metadata: DocumentMetadata
    content_hash: str

def compute_hash(text: str) -> str:
    """Generate SHA256 signature for text data."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def extract_file_metadata(file_path: str, content: str) -> Dict[str, Any]:
    """Extract metadata from the raw file and parsed content."""
    stats = os.stat(file_path)
    file_name = os.path.basename(file_path)
    ext = os.path.splitext(file_name)[1].lower()
    
    word_count = len(content.split())
    char_count = len(content)
    
    return {
        "file_name": file_name,
        "file_path": os.path.abspath(file_path),
        "file_type": ext.lstrip("."),
        "file_size_bytes": stats.st_size,
        "word_count": word_count,
        "char_count": char_count,
        "created_at_epoch": stats.st_ctime,
        "modified_at_epoch": stats.st_mtime,
    }
