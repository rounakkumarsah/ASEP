"""
ASEP -- Projects Router
========================
Manage projects within an Organization.
API Keys are scoped to Projects.
"""
from __future__ import annotations

import logging
import re
import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from src.auth.dependencies import CurrentUser
from src.db.models.project import Project
from src.db.models.user import User
from src.db.postgres import DbSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects"])


def _slugify(name: str) -> str:
    """Convert a name to a URL-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug[:100]


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class ProjectResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    is_active: bool
    model_config = {"from_attributes": True}


class UpdateProjectRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: CreateProjectRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> ProjectResponse:
    """Create a new project within the current user's organization."""
    org_id = current_user.org_id
    if not org_id:
        user_res = await db.execute(select(User).where(User.id == current_user.id))
        user_obj = user_res.scalar_one_or_none()
        if user_obj:
            org_id = user_obj.org_id

    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must be a member of an organization to create projects.",
        )

    slug_base = _slugify(payload.name)
    slug = slug_base
    counter = 1
    while True:
        existing = await db.execute(
            select(Project).where(
                Project.org_id == org_id,
                Project.slug == slug,
            )
        )
        if not existing.scalar_one_or_none():
            break
        slug = f"{slug_base}-{counter}"
        counter += 1

    project = Project(
        id=uuid.uuid4(),
        org_id=org_id,
        name=payload.name,
        slug=slug,
        description=payload.description,
        is_active=True,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)

    logger.info("Project created", extra={"project_id": str(project.id), "org_id": str(project.org_id)})
    return ProjectResponse.model_validate(project)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    current_user: CurrentUser,
    db: DbSession,
) -> list[ProjectResponse]:
    """List all projects in the current user's organization."""
    if not current_user.org_id:
        return []

    result = await db.execute(
        select(Project)
        .where(Project.org_id == current_user.org_id, Project.is_active == True)  # noqa: E712
        .order_by(Project.created_at.desc())
        .limit(100)
    )
    projects = list(result.scalars().all())
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ProjectResponse:
    """Get a single project by ID."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if current_user.org_id and project.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    payload: UpdateProjectRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> ProjectResponse:
    """Update project name or description."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if current_user.org_id and project.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description
    await db.flush()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_200_OK)
async def delete_project(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """Soft-delete a project (sets is_active=False)."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if current_user.org_id and project.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    project.is_active = False
    await db.flush()
    logger.info("Project deactivated", extra={"project_id": str(project_id)})
    return {"detail": "Project deactivated."}
