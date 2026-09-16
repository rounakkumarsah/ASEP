"""
ASEP — Local Workspace & IDE Bridge Router
==========================================
Enables VS Code Extension to sync local workspace absolute paths, explore files,
and bridge local editor projects directly with the ASEP multi-agent engine.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger("opensep.workspace")

router = APIRouter(prefix="/workspace", tags=["Workspace Bridge"])


class WorkspaceSyncRequest(BaseModel):
    workspace_path: str = Field(..., description="Absolute path of the workspace opened in VS Code")
    workspace_name: str | None = Field(default=None, description="Display name of the workspace")
    timestamp: str | None = Field(default=None, description="ISO timestamp of sync request")


class FileEntry(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int


class WorkspaceFilesResponse(BaseModel):
    root_path: str
    total_entries: int
    entries: list[FileEntry]


# Global state for current active IDE workspace bridge
_ACTIVE_WORKSPACE: dict[str, Any] = {
    "workspace_path": os.getcwd(),
    "workspace_name": "Default Workspace",
    "synced_at": None,
}


@router.post("/sync", status_code=status.HTTP_200_OK)
async def sync_workspace(payload: WorkspaceSyncRequest) -> dict[str, Any]:
    """Receives absolute directory path from VS Code and binds it to ASEP engine."""
    clean_path = os.path.abspath(payload.workspace_path)
    if not os.path.exists(clean_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace path does not exist on host: {clean_path}",
        )

    _ACTIVE_WORKSPACE["workspace_path"] = clean_path
    _ACTIVE_WORKSPACE["workspace_name"] = payload.workspace_name or os.path.basename(clean_path)
    _ACTIVE_WORKSPACE["synced_at"] = payload.timestamp

    # Update WORKSPACE_ROOT for local execution
    os.environ["WORKSPACE_ROOT"] = clean_path

    logger.info("IDE Workspace Synced: %s (Name: %s)", clean_path, _ACTIVE_WORKSPACE["workspace_name"])

    return {
        "status": "synced",
        "workspace_path": clean_path,
        "workspace_name": _ACTIVE_WORKSPACE["workspace_name"],
        "message": f"Successfully bound ASEP file explorer to {clean_path}",
    }


@router.get("/info", status_code=status.HTTP_200_OK)
async def get_workspace_info() -> dict[str, Any]:
    """Returns currently bound IDE workspace information."""
    return _ACTIVE_WORKSPACE


@router.get("/files", response_model=WorkspaceFilesResponse)
async def list_workspace_files(subpath: str = "") -> WorkspaceFilesResponse:
    """Explores files and directories inside the synced workspace for the IDE file explorer."""
    root = _ACTIVE_WORKSPACE.get("workspace_path") or os.getcwd()
    target_dir = os.path.abspath(os.path.join(root, subpath)) if subpath else root

    # Prevent directory traversal outside root
    if not target_dir.startswith(root):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Path outside active workspace root.",
        )

    if not os.path.isdir(target_dir):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Directory not found: {target_dir}",
        )

    entries: list[FileEntry] = []
    try:
        with os.scandir(target_dir) as it:
            for item in it:
                # Skip hidden/git folders
                if item.name.startswith((".", "node_modules", "__pycache__", "venv")):
                    continue
                try:
                    stat = item.stat()
                    entries.append(
                        FileEntry(
                            name=item.name,
                            path=item.path,
                            is_dir=item.is_dir(),
                            size=stat.st_size if not item.is_dir() else 0,
                        )
                    )
                except OSError:
                    continue
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading directory: {exc}",
        ) from exc

    # Sort directories first, then files
    entries.sort(key=lambda x: (not x.is_dir, x.name.lower()))

    return WorkspaceFilesResponse(
        root_path=target_dir,
        total_entries=len(entries),
        entries=entries,
    )