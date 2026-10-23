"""
Dynamic Workspace Path Helper for ASEP.
Ensures file writing uses /tmp/workspaces in serverless environments (Vercel, AWS Lambda)
where the root file system (/var/task) is read-only, while preserving local development paths.
"""
import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def get_workspaces_dir() -> Path:
    """Return the base path for workspaces, dynamically adapting to serverless environments (e.g. Vercel, AWS Lambda)."""
    # Check if running on Vercel or AWS Lambda
    is_serverless = os.environ.get("VERCEL") == "1" or os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None

    if is_serverless:
        # Vercel only allows writes to /tmp
        print("Using /tmp/workspaces for Vercel")
        logger.info("Using /tmp/workspaces for Vercel")
        base_dir = Path("/tmp/workspaces")
    else:
        # Local dev
        workspace_root = os.environ.get("WORKSPACE_ROOT")
        if workspace_root:
            ws_path = Path(workspace_root)
            base_dir = ws_path if ws_path.name == "workspaces" else ws_path / "workspaces"
        else:
            repo_root = Path(__file__).resolve().parent.parent.parent.parent
            base_dir = repo_root / "workspaces"

    try:
        base_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning("Could not create workspaces directory at %s: %s; falling back to tempdir", base_dir, e)
        base_dir = Path(tempfile.gettempdir()) / "workspaces"
        base_dir.mkdir(parents=True, exist_ok=True)

    return base_dir
