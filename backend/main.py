"""
ASEP Backend — Application Entry Point for Vercel / ASGI Deployments
=====================================================================
Exposes the top-level `app` ASGI handler required by Vercel Serverless Functions
and ASGI servers (uvicorn/gunicorn).
"""

from __future__ import annotations

import os
import sys

# Ensure backend root directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import the initialized FastAPI app instance
from src.main import app

__all__ = ["app"]
