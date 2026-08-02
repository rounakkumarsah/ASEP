import time
import sys
import platform
import subprocess
from fastapi import APIRouter
from src.config.settings import get_settings

router = APIRouter()
START_TIME = time.time()

def get_git_commit() -> str:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return commit.decode("utf-8").strip()
    except Exception:
        return "unknown"

import os

@router.get("/diagnostics")
async def get_diagnostics():
    settings = get_settings()
    uptime = time.time() - START_TIME
    
    return {
        "build_version": settings.APP_VERSION,
        "git_commit": get_git_commit(),
        "environment": settings.APP_ENV,
        "uptime_seconds": round(uptime, 2),
        "runtime": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "sys_platform": sys.platform,
        }
    }

@router.get("/sentry-debug")
async def trigger_sentry_error():
    """Trigger a test exception to verify Sentry error logging."""
    settings = get_settings()
    has_dsn = bool(settings.SENTRY_DSN_BACKEND or os.getenv("SENTRY_DSN_BACKEND"))
    if not has_dsn:
        return {"status": "SENTRY_DSN_BACKEND is not configured on this server.", "working": False}
    # Intentional test exception to verify Sentry capture
    division_by_zero = 1 / 0
    return {"result": division_by_zero}
