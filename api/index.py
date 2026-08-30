"""
Vercel ASGI entry point for ASEP FastAPI backend.

Vercel discovers the `app` variable from this file.
The `api/` directory at the monorepo root means Vercel's file-system
router automatically maps all /api/* requests here.

Import chain:
  api/index.py -> backend/main.py -> backend/src/main.py -> FastAPI app
"""
import sys
import os

# Add the backend directory to sys.path so `from src.main import app` resolves.
# __file__ is /var/task/api/index.py on Vercel; backend is at ../backend/
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# backend/main.py itself also inserts its own directory into sys.path,
# then does `from src.main import app` which creates the FastAPI app.
import main as _backend_main  # noqa: F401

app = _backend_main.app

__all__ = ["app"]
