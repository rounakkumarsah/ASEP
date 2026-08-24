import os
import tempfile

from src.documents.loaders import LogLoader, PPTXLoader, get_loader_for_file
from src.documents.ocr import OCRImageLoader


def test_pptx_loader_fallback():
    loader = get_loader_for_file("presentation.pptx")
    assert isinstance(loader, PPTXLoader)
    content = loader.load("presentation.pptx")
    assert "pptx" in content.lower()

def test_log_loader():
    with tempfile.NamedTemporaryFile(suffix=".log", mode="w", delete=False) as f:
        f.write("INFO: healthy connection\nERROR: database failed connection\nTRACEBACK: file app.py line 12\n")
        temp_path = f.name

    try:
        loader = get_loader_for_file(temp_path)
        assert isinstance(loader, LogLoader)
        content = loader.load(temp_path)
        assert "ERROR" in content
        assert "TRACEBACK" in content
        assert "INFO" not in content
    finally:
        os.remove(temp_path)

def test_ocr_image_loader_confidence():
    loader = OCRImageLoader()
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        temp_path = f.name

    try:
        text, conf = loader.load_with_confidence(temp_path)
        assert conf > 0.0
        assert text != ""
    finally:
        os.remove(temp_path)
