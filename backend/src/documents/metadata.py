"""
ASEP — Document Metadata Extraction
"""

import os
from typing import Any


def extract_file_metadata(file_path: str, content: str) -> dict[str, Any]:
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
