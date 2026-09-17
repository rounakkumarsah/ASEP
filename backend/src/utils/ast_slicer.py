"""
ASEP — AST Slicing Engine
=========================
Parses source files into Abstract Syntax Tree (AST) node hierarchies
and extracts ONLY relevant function/class slices before sending code
context to any agent. Eliminates full-file context waste when only
a single function or class is modified or referenced.
"""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ASTSliceResult:
    """Detailed telemetry and code payload of an AST slicing operation."""
    sliced_content: str
    original_lines: int
    sliced_lines: int
    original_tokens: int
    sliced_tokens: int
    token_reduction_pct: float
    extracted_symbols: list[str] = field(default_factory=list)
    is_sliced: bool = True
    language: str = "python"


def estimate_tokens(text: str) -> int:
    """Accurately estimate token count (approx. 4 characters per token)."""
    if not text:
        return 0
    # Average token length across code and prose is ~3.8 - 4.0 chars
    return max(1, len(text) // 4)


class ASTSlicer:
    """Extracts targeted function/class AST nodes from source files."""

    @classmethod
    def slice_code(
        cls,
        source_code: str,
        filename: str = "main.py",
        target_symbol: str | None = None,
        changed_lines: list[int] | None = None,
    ) -> ASTSliceResult:
        """Parse source code and extract only the relevant symbol or changed line ranges.

        If target_symbol is provided, locates that specific function/class AST node.
        If changed_lines is provided, locates AST nodes overlapping those lines.
        If both are None, scans for functions/classes mentioned in context or returns source.
        """
        orig_lines = source_code.count("\n") + 1
        orig_tokens = estimate_tokens(source_code)

        # 1. Handle Python files via built-in ast module
        if filename.endswith((".py", ".pyw")):
            return cls._slice_python(
                source_code=source_code,
                filename=filename,
                target_symbol=target_symbol,
                changed_lines=changed_lines,
                orig_lines=orig_lines,
                orig_tokens=orig_tokens,
            )

        # 2. Language-agnostic fallback for JS/TS/Go/Rust/etc.
        return cls._slice_generic(
            source_code=source_code,
            filename=filename,
            target_symbol=target_symbol,
            changed_lines=changed_lines,
            orig_lines=orig_lines,
            orig_tokens=orig_tokens,
        )

    @classmethod
    def _slice_python(
        cls,
        source_code: str,
        filename: str,
        target_symbol: str | None,
        changed_lines: list[int] | None,
        orig_lines: int,
        orig_tokens: int,
    ) -> ASTSliceResult:
        try:
            tree = ast.parse(source_code, filename=filename)
        except SyntaxError as err:
            logger.warning("AST parse syntax error in %s: %s; falling back to generic slicing", filename, err)
            return cls._slice_generic(source_code, filename, target_symbol, changed_lines, orig_lines, orig_tokens)

        source_lines = source_code.splitlines(keepends=True)
        nodes_to_extract: list[tuple[int, int, str]] = []  # (start_line, end_line, symbol_name)

        # Traverse top-level and class-level nodes
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                node_name = node.name
                start_line = getattr(node, "lineno", None)
                end_line = getattr(node, "end_lineno", None)

                # Decorators start earlier than lineno
                if hasattr(node, "decorator_list") and node.decorator_list:
                    dec_starts = [getattr(d, "lineno", start_line) for d in node.decorator_list if hasattr(d, "lineno")]
                    if dec_starts:
                        start_line = min(dec_starts)

                if start_line is None or end_line is None:
                    continue

                # Condition A: Target symbol matched
                if target_symbol and node_name.lower() == target_symbol.lower():
                    nodes_to_extract.append((start_line, end_line, node_name))
                    break

                # Condition B: Overlaps changed lines
                if changed_lines:
                    if any(start_line <= ln <= end_line for ln in changed_lines):
                        nodes_to_extract.append((start_line, end_line, node_name))

        # If no targeted node found and file is large (> 60 lines), try to extract top symbol
        if not nodes_to_extract and target_symbol:
            # Look for partial matches
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if target_symbol.lower() in node.name.lower():
                        start_line = getattr(node, "lineno", 1)
                        end_line = getattr(node, "end_lineno", len(source_lines))
                        nodes_to_extract.append((start_line, end_line, node.name))
                        break

        # If still nothing matched, return full content
        if not nodes_to_extract:
            return ASTSliceResult(
                sliced_content=source_code,
                original_lines=orig_lines,
                sliced_lines=orig_lines,
                original_tokens=orig_tokens,
                sliced_tokens=orig_tokens,
                token_reduction_pct=0.0,
                extracted_symbols=[],
                is_sliced=False,
                language="python",
            )

        # Deduplicate & sort node ranges
        nodes_to_extract.sort(key=lambda x: x[0])
        extracted_chunks: list[str] = []
        extracted_names: list[str] = []
        total_sliced_lines = 0

        for start, end, name in nodes_to_extract:
            extracted_names.append(name)
            # 1-indexed to 0-indexed slicing
            chunk = "".join(source_lines[start - 1 : end])
            chunk_line_count = end - start + 1
            total_sliced_lines += chunk_line_count

            header = (
                f"# --- AST Slice: {name} ({filename}:L{start}-L{end}) ---\n"
            )
            extracted_chunks.append(f"{header}{chunk}\n")

        sliced_code = "\n".join(extracted_chunks).strip()
        sliced_tokens = estimate_tokens(sliced_code)
        reduction_pct = round(max(0.0, (1.0 - (sliced_tokens / max(1, orig_tokens))) * 100.0), 1)

        summary_banner = (
            f"# [AST SLICE ACTIVE] Extracted {len(extracted_names)} node(s): {', '.join(extracted_names)}\n"
            f"# File: {filename} | {total_sliced_lines}/{orig_lines} lines | "
            f"{sliced_tokens}/{orig_tokens} tokens ({reduction_pct}% reduction)\n\n"
        )
        final_payload = summary_banner + sliced_code

        logger.info(
            "[AST Slicer] Sliced %s: extracted symbols %s (%d/%d lines, %d%% token reduction)",
            filename,
            extracted_names,
            total_sliced_lines,
            orig_lines,
            reduction_pct,
        )

        return ASTSliceResult(
            sliced_content=final_payload,
            original_lines=orig_lines,
            sliced_lines=total_sliced_lines,
            original_tokens=orig_tokens,
            sliced_tokens=estimate_tokens(final_payload),
            token_reduction_pct=reduction_pct,
            extracted_symbols=extracted_names,
            is_sliced=True,
            language="python",
        )

    @classmethod
    def _slice_generic(
        cls,
        source_code: str,
        filename: str,
        target_symbol: str | None,
        changed_lines: list[int] | None,
        orig_lines: int,
        orig_tokens: int,
    ) -> ASTSliceResult:
        """Language-agnostic bracket/indent matching for JS, TS, Go, etc."""
        if not target_symbol:
            return ASTSliceResult(
                sliced_content=source_code,
                original_lines=orig_lines,
                sliced_lines=orig_lines,
                original_tokens=orig_tokens,
                sliced_tokens=orig_tokens,
                token_reduction_pct=0.0,
                extracted_symbols=[],
                is_sliced=False,
                language="generic",
            )

        lines = source_code.splitlines(keepends=True)
        pattern = re.compile(
            rf"(?:function|class|const|let|var|async\s+function|def)\s+{re.escape(target_symbol)}\b",
            re.IGNORECASE,
        )

        start_idx = None
        for idx, line in enumerate(lines):
            if pattern.search(line):
                start_idx = idx
                break

        if start_idx is None:
            return ASTSliceResult(
                sliced_content=source_code,
                original_lines=orig_lines,
                sliced_lines=orig_lines,
                original_tokens=orig_tokens,
                sliced_tokens=orig_tokens,
                token_reduction_pct=0.0,
                extracted_symbols=[],
                is_sliced=False,
                language="generic",
            )

        # Scan matching braces {}
        open_braces = 0
        found_first_brace = False
        end_idx = len(lines) - 1

        for idx in range(start_idx, len(lines)):
            line = lines[idx]
            for ch in line:
                if ch == "{":
                    open_braces += 1
                    found_first_brace = True
                elif ch == "}":
                    open_braces -= 1
                    if found_first_brace and open_braces <= 0:
                        end_idx = idx
                        break
            if found_first_brace and open_braces <= 0:
                break

        sliced_lines_list = lines[start_idx : end_idx + 1]
        sliced_text = "".join(sliced_lines_list).strip()
        sliced_tokens = estimate_tokens(sliced_text)
        reduction_pct = round(max(0.0, (1.0 - (sliced_tokens / max(1, orig_tokens))) * 100.0), 1)

        banner = (
            f"// [AST SLICE ACTIVE] Extracted symbol: {target_symbol}\n"
            f"// File: {filename} | {len(sliced_lines_list)}/{orig_lines} lines | "
            f"{sliced_tokens}/{orig_tokens} tokens ({reduction_pct}% reduction)\n\n"
        )
        final_payload = banner + sliced_text

        logger.info(
            "[AST Slicer] Generic sliced %s for %s (%d/%d lines, %d%% token reduction)",
            filename,
            target_symbol,
            len(sliced_lines_list),
            orig_lines,
            reduction_pct,
        )

        return ASTSliceResult(
            sliced_content=final_payload,
            original_lines=orig_lines,
            sliced_lines=len(sliced_lines_list),
            original_tokens=orig_tokens,
            sliced_tokens=estimate_tokens(final_payload),
            token_reduction_pct=reduction_pct,
            extracted_symbols=[target_symbol],
            is_sliced=True,
            language="generic",
        )
