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
