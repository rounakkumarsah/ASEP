"""
ASEP — Skills API Router
========================
Endpoints for managing built-in and user-defined Agent Skills,
including CRUD, file attachments, version restore, export/import,
and runtime simulation.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile, status
from pydantic import BaseModel, Field

from src.skills import skill_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])


class CreateSkillRequest(BaseModel):
    name: str = Field(..., description="Unique skill name slug (e.g. django-rest-expert)")
    description: str = Field("", description="Short summary of what this skill does")
    trigger: str = Field("", description="Trigger keywords or phrases")
    instructions: str = Field(..., description="Markdown instructions to inject into agent prompt")
    dependencies: list[str] = Field(default_factory=list, description="Other skills to also apply")
    scope: str = Field("workspace", description="'workspace' or 'project'")
    project_id: str | None = Field(None, description="Linked project ID if project-scoped")
    enabled: bool = Field(True, description="Whether skill is currently active")


class UpdateSkillRequest(BaseModel):
    description: str | None = None
    trigger: str | None = None
    instructions: str | None = None
    dependencies: list[str] | None = None
    scope: str | None = None
    project_id: str | None = None
    enabled: bool | None = None


class ToggleSkillRequest(BaseModel):
    enabled: bool


class TestSkillRequest(BaseModel):
    sample_goal: str = Field(..., description="Sample user prompt to test skill against")


class RestoreVersionRequest(BaseModel):
    version_idx: int = Field(0, description="Index in version_history to restore")


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("", response_model=list[dict[str, Any]])
async def list_skills(
    project_id: str | None = Query(None, description="Filter by project ID"),
    scope: str | None = Query(None, description="Filter by scope ('builtin', 'user', 'workspace', 'project', 'all')"),
    search: str | None = Query(None, description="Search keyword in name/description/trigger"),
) -> list[dict[str, Any]]:
    """List all available skills matching the given filters."""
    skills = skill_manager.list_skills(project_id=project_id, scope=scope, search=search)
    return [s.to_dict() for s in skills]


@router.get("/{name}", response_model=dict[str, Any])
async def get_skill(name: str) -> dict[str, Any]:
    """Retrieve details for a single skill."""
    skill = skill_manager.get_skill(name)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{name}' not found")
    return skill.to_dict()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=dict[str, Any])
async def create_skill(payload: CreateSkillRequest) -> dict[str, Any]:
    """Create a new user skill."""
    try:
        skill = skill_manager.create_skill(payload.model_dump())
        return skill.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put("/{name}", response_model=dict[str, Any])
async def update_skill(name: str, payload: UpdateSkillRequest) -> dict[str, Any]:
    """Update a user skill (built-in skills are read-only)."""
    try:
        data = {k: v for k, v in payload.model_dump().items() if v is not None}
        skill = skill_manager.update_skill(name, data)
        return skill.to_dict()
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{name}' not found")
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{name}")
async def delete_skill(name: str) -> dict[str, Any]:
    """Delete a user skill (built-in skills are protected)."""
    try:
        success = skill_manager.delete_skill(name)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{name}' not found")
        return {"status": "deleted", "name": name}
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post("/{name}/toggle", response_model=dict[str, Any])
async def toggle_skill(name: str, payload: ToggleSkillRequest) -> dict[str, Any]:
    """Enable or disable a skill."""
    try:
        skill = skill_manager.toggle_skill(name, payload.enabled)
        return skill.to_dict()
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{name}' not found")


@router.post("/{name}/duplicate", response_model=dict[str, Any])
async def duplicate_skill(name: str) -> dict[str, Any]:
    """Duplicate any skill as an editable user skill."""
    try:
        duplicated = skill_manager.duplicate_skill(name)
        return duplicated.to_dict()
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{name}' not found")


@router.get("/{name}/export")
async def export_skill(
    name: str,
    format: str = Query("md", description="'md' or 'zip'"),
) -> Response:
    """Export skill as .md or ZIP archive with attachments."""
    try:
        filename, data = skill_manager.export_skill(name, format_type=format)
        media_type = "application/zip" if filename.endswith(".zip") else "text/markdown"
        return Response(
            content=data,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{name}' not found")


@router.post("/import", response_model=dict[str, Any])
async def import_skill(file: UploadFile = File(...)) -> dict[str, Any]:
    """Import a skill from an uploaded .md or .zip file."""
    try:
        content = await file.read()
        imported = skill_manager.import_skill(content, file.filename or "skill.md")
        return imported.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{name}/test", response_model=dict[str, Any])
async def test_skill(name: str, payload: TestSkillRequest) -> dict[str, Any]:
    """Test skill activation against sample goal and return simulated injected prompt."""
    try:
        return skill_manager.test_skill(name, payload.sample_goal)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{name}' not found")


@router.post("/{name}/attachments", response_model=dict[str, Any])
async def upload_attachment(name: str, file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload a reference document (PDF, DOCX, TXT, code) to a skill."""
    try:
        content = await file.read()
        filename = file.filename or "attachment.txt"
        att = skill_manager.add_attachment(name, filename, content)
        return att.to_dict()
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{name}' not found")
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{name}/attachments/{filename}")
async def delete_attachment(name: str, filename: str) -> dict[str, Any]:
    """Delete an attachment from a skill."""
    success = skill_manager.delete_attachment(name, filename)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Attachment '{filename}' not found")
    return {"status": "deleted", "filename": filename}


@router.post("/{name}/restore-version", response_model=dict[str, Any])
async def restore_version(name: str, payload: RestoreVersionRequest) -> dict[str, Any]:
    """Restore skill instructions and attachments from version history."""
    try:
        restored = skill_manager.restore_version(name, payload.version_idx)
        return restored.to_dict()
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{name}' not found")
    except (IndexError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
