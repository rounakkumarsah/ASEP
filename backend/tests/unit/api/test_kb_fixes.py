import pytest
import os
import magic
from src.utils.security_scanner import secure_filename
from src.documents.hybrid_retrieval import ReciprocalRankFusion

def test_magic_byte_validation():
    # Valid mime type
    assert magic.from_buffer(b"%PDF-1.4\n", mime=True) == "application/pdf"
    # Invalid mime type (binary/executable detected as octet-stream or x-dosexec)
    invalid_mime = magic.from_buffer(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00", mime=True)
    assert invalid_mime in ("application/x-dosexec", "application/octet-stream")
    assert invalid_mime not in ["application/pdf", "text/plain"]

def test_secure_filename():
    assert secure_filename("my file @#$%^.txt") == "my_file_.txt"
    assert secure_filename("../../../etc/passwd") == "etc_passwd"

def test_rrf_fusion():
    list1 = [{"id": "doc1", "content": "hello"}, {"id": "doc2", "content": "world"}]
    list2 = [{"id": "doc2", "content": "world"}, {"id": "doc3", "content": "test"}]
    fused = ReciprocalRankFusion.fuse([list1, list2], k=60)
    # doc2 appears in both, should have higher score
    assert fused[0]["id"] == "doc2"
