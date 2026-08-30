"""
Vercel entry point for ASEP FastAPI backend.
Vercel's Python runtime discovers `app` from this file.
The `api/` directory is at the monorepo root so Vercel's
file-system router maps /api/* -> here automatically.
"""
import sys
import os

# Make `backend/` importable so all `src.*` imports resolve correctly
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
backend_dir = os.path.abspath(backend_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.main import app  # noqa: F401 — Vercel discovers `app`

__all__ = ["app"]
