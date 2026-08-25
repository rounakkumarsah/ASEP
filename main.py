"""
ASEP — Top-Level Application Entry Point for Vercel / ASGI Deployments
=====================================================================
Exposes the top-level `app` ASGI handler.
"""

from __future__ import annotations

import os
import sys

# Ensure backend directory is in sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(root_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.main import app

__all__ = ["app"]
