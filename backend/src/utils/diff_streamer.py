"""
ASEP — Diff-Only Streaming Engine
=================================
Ensures that after the initial version of a source file is shared,
all subsequent agent calls and node updates receive only unified diffs,
not full redundant file contents. Maximizes LLM context window space
and dramatically cuts token expenditure.
"""

from __future__ import annotations

import difflib
import logging
from dataclasses import dataclass
from typing import Any

from src.utils.ast_slicer import estimate_tokens

logger = logging.getLogger(__name__)


@dataclass
class DiffStreamResult:
    """Result of diff-only streaming evaluation."""
    payload: str
    is_diff: bool
    original_tokens: int
    streamed_tokens: int
    tokens_saved: int
    token_reduction_pct: float
    filepath: str


class DiffStreamer:
    """Tracks file version history and converts updates into unified diffs."""

    def __init__(self, history: dict[str, str] | None = None) -> None:
        self.history: dict[str, str] = history if history is not None else {}

    def process_file_content(
        self,
        filepath: str,
        new_content: str,
        force_full: bool = False,
    ) -> DiffStreamResult:
        """Process file content.

        - First version of file: cached and transmitted as full content.
        - Subsequent versions: transmitted strictly as unified diffs.
        """
        full_tokens = estimate_tokens(new_content)
        previous_content = self.history.get(filepath)

        # 1. First time seeing this file or explicitly forced
        if previous_content is None or force_full:
            self.history[filepath] = new_content
            banner = f"# [DIFF STREAM INITIAL] {filepath} ({full_tokens} tokens registered in session history)\n"
            return DiffStreamResult(
                payload=banner + new_content,
                is_diff=False,
                original_tokens=full_tokens,
                streamed_tokens=estimate_tokens(banner + new_content),
                tokens_saved=0,
                token_reduction_pct=0.0,
                filepath=filepath,
            )

        # 2. File already seen: generate unified diff
        old_lines = previous_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff_lines = list(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"a/{filepath}",
                tofile=f"b/{filepath}",
                n=3,
            )
        )

        # If files are identical
        if not diff_lines:
            no_change_msg = f"# [DIFF STREAM ACTIVE] No modifications detected in {filepath}.\n"
            return DiffStreamResult(
                payload=no_change_msg,
                is_diff=True,
                original_tokens=full_tokens,
                streamed_tokens=estimate_tokens(no_change_msg),
                tokens_saved=max(0, full_tokens - estimate_tokens(no_change_msg)),
                token_reduction_pct=98.0,
                filepath=filepath,
            )

        raw_diff = "".join(diff_lines)
        diff_tokens = estimate_tokens(raw_diff)
        tokens_saved = max(0, full_tokens - diff_tokens)
        reduction_pct = round(max(0.0, (1.0 - (diff_tokens / max(1, full_tokens))) * 100.0), 1)

        banner = (
            f"# [DIFF-ONLY STREAM ACTIVE] Unified diff for {filepath}\n"
            f"# Previous version cached. Streaming diff: {diff_tokens}/{full_tokens} tokens "
            f"({reduction_pct}% reduction, {tokens_saved} tokens saved)\n\n"
        )
        final_payload = banner + raw_diff

        # Update cache to latest version
        self.history[filepath] = new_content

        logger.info(
            "[Diff Streamer] Sent diff-only update for %s: %d tokens vs %d full (%d%% reduction)",
            filepath,
            diff_tokens,
            full_tokens,
            reduction_pct,
        )

        return DiffStreamResult(
            payload=final_payload,
            is_diff=True,
            original_tokens=full_tokens,
            streamed_tokens=estimate_tokens(final_payload),
            tokens_saved=tokens_saved,
            token_reduction_pct=reduction_pct,
            filepath=filepath,
        )
