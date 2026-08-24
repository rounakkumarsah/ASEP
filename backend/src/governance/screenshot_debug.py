import logging
import re
from typing import Any

from src.documents.ocr import OCRImageLoader
from src.production.graphrag_engine import LocalGraphRAGEngine

logger = logging.getLogger(__name__)

class ScreenshotDebugger:
    """Performs optical character recognition (OCR) and filters system error trace blocks."""

    def __init__(self, ocr_loader: OCRImageLoader | None = None, graphrag_engine: LocalGraphRAGEngine | None = None) -> None:
        self.ocr = ocr_loader or OCRImageLoader()
        self.graphrag = graphrag_engine or LocalGraphRAGEngine()

    def detect_stack_trace(self, text: str) -> tuple[str | None, str | None]:
        """Parses python, javascript, node, or bash error blocks."""
        # Check python traceback signatures
        py_match = re.search(r'(Traceback\s*\(most\s*recent\s*call\s*last\):.*)', text, re.DOTALL | re.IGNORECASE)
        if py_match:
            return py_match.group(1).strip(), "python"

        # Check JS/Node stack trace signatures
        js_match = re.search(r'(Error:.*?\bat\s+.*)', text, re.DOTALL | re.IGNORECASE)
        if js_match:
            return js_match.group(1).strip(), "javascript"

        # Check raw ECONNREFUSED or socket patterns
        econn_match = re.search(r'(ECONNREFUSED.*|ConnectionError.*)', text, re.DOTALL | re.IGNORECASE)
        if econn_match:
            return econn_match.group(1).strip(), "bash"

        return None, None

    async def debug_screenshot(self, file_path: str) -> dict[str, Any]:
        """Runs the complete OCR traceback detection and retrieves cached solution recommendations."""
        logger.info(f"Analyzing screenshot for debug clues: {file_path}")

        # 1. OCR Extract
        extracted_text, confidence = self.ocr.load_with_confidence(file_path)

        # 2. Extract error segment & language clues
        error_block, language = self.detect_stack_trace(extracted_text)

        # 3. If traceback is found, search semantic cache
        cache_hit = False
        solution = None
        if error_block:
            query = error_block
            try:
                cache_result = await self.graphrag.get_semantic_cache(query)
                if cache_result.is_hit:
                    cache_hit = True
                    solution = cache_result.cached_solution
            except Exception as exc:
                logger.debug(f"Bypassing semantic cache check: {exc}")
        else:
            query = extracted_text

        # If cache missed, fall back to mock recommendation logic
        if not solution:
            if language == "python" or "connectionerror" in query.lower():
                solution = "Recommended Fix: Verify your Redis/PostgreSQL container connection endpoints in settings.py."
            else:
                solution = f"Recommended Fix: Review logs matching parsed query parameters: {query[:100]}"

        return {
            "file_path": file_path,
            "ocr_confidence": confidence,
            "error_detected": error_block is not None,
            "error_block": error_block,
            "language_detected": language,
            "semantic_cache_hit": cache_hit,
            "recommended_fix": solution,
        }
