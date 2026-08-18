"""
ASEP — Vercel Serverless API Gateway Entrypoint
================================================
Exposes the FastAPI application instance for Vercel Serverless Python runtime.
Imports sys/path modifications to locate backend package seamlessly.
"""

import sys
import os

# Include backend in Python module search path for Vercel
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

try:
    from src.api.app import create_app
except ImportError:
    from backend.src.api.app import create_app

app = create_app()
