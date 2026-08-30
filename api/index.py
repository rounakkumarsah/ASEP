"""
Vercel ASGI entry point — ASEP FastAPI backend.

Vercel discovers `app` from this file.
The /api/* prefix in vercel.json rewrites routes here.

Path resolution:
  On Vercel: /var/task/api/index.py  ?  backend/ at /var/task/backend/
  The includeFiles glob in vercel.json bundles backend/** into the function.
"""
import sys
import os

# /var/task is Vercel's working directory. backend/ is bundled next to api/
# because of includeFiles: "backend/**" in vercel.json functions config.
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_backend = os.path.join(_root, "backend")

for _p in [_root, _backend]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# backend/main.py re-adds backend/ to sys.path and does `from src.main import app`
try:
    import main as _m
    app = _m.app
except Exception as e:
    # Fallback: create a minimal emergency app so Vercel at least returns JSON errors
    from fastapi import FastAPI
    app = FastAPI(title="ASEP [STARTUP ERROR]")

    @app.get("/health")
    async def health():
        return {"status": "error", "detail": str(e)}

    @app.get("/api/v1/health")
    async def health_v1():
        return {"status": "error", "detail": str(e)}

__all__ = ["app"]
