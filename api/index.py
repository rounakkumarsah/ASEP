import os
import sys
import logging
import traceback

logger = logging.getLogger("asep.vercel")

# Resolve candidate paths for Vercel Serverless environment
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
_backend = os.path.join(_root, "backend")
_backend_src = os.path.join(_backend, "src")

candidate_paths = [
    _backend,
    _backend_src,
    _root,
    _here,
    "/var/task",
    "/var/task/backend",
    "/var/task/backend/src",
]

for p in candidate_paths:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

# Locate skills directory
for s_dir in [
    os.path.join(_root, "skills"),
    os.path.join(_backend, "skills"),
    "/var/task/skills",
    "/var/task/backend/skills",
]:
    if os.path.isdir(s_dir):
        os.environ.setdefault("ASEP_SKILLS_DIR", s_dir)
        break

app = None

# Attempt to load the application instance
try:
    from src.api.app import create_app
    app = create_app()
    logger.info("FastAPI application loaded successfully via src.api.app:create_app")
except Exception as exc1:
    logger.warning("Failed to import via src.api.app: %s", exc1)
    try:
        from backend.main import app as _app
        app = _app
        logger.info("FastAPI application loaded successfully via backend.main:app")
    except Exception as exc2:
        logger.warning("Failed to import via backend.main: %s", exc2)
        try:
            import main
            app = main.app
            logger.info("FastAPI application loaded successfully via main:app")
        except Exception as exc3:
            logger.error("All app imports failed: exc1=%s, exc2=%s, exc3=%s", exc1, exc2, exc3)
            # Create a diagnostic fallback FastAPI app to report the exact stack trace
            from fastapi import FastAPI
            from fastapi.responses import JSONResponse

            app = FastAPI(title="ASEP Emergency Diagnostics")
            tb1 = traceback.format_exception(type(exc1), exc1, exc1.__traceback__)
            tb2 = traceback.format_exception(type(exc2), exc2, exc2.__traceback__)
            tb3 = traceback.format_exception(type(exc3), exc3, exc3.__traceback__)

            @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
            async def fallback_diagnostics(full_path: str):
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Backend initialization failed on Vercel",
                        "tracebacks": {
                            "src_api_app": "".join(tb1),
                            "backend_main": "".join(tb2),
                            "main": "".join(tb3),
                        },
                        "sys_path": sys.path,
                        "current_dir": os.getcwd(),
                    }
                )
