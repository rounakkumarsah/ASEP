"""
ASEP -- API Keys Router
========================
Project-scoped API key management.

Security guarantees:
  - Full key is generated once and NEVER stored in the database.
  - Only the SHA-256 hash and display prefix are persisted.
  - The full key is returned ONCE in the create response only.
  - Revoked keys keep their row for audit purposes (is_active=False).
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUser
from src.db.models.api_key import ApiKey
from src.db.models.project import Project
from src.db.postgres import DbSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Human label for this key.")
    project_id: uuid.UUID = Field(..., description="Project this key is scoped to.")
    scopes: list[str] | None = Field(default=None, description="Optional permission scopes.")


class ApiKeyCreatedResponse(BaseModel):
    """Returned ONCE on creation — includes the full key."""
    id: uuid.UUID
    name: str
    key_prefix: str
    full_key: str = Field(description="The complete API key. Store it now — it will NOT be shown again.")
    project_id: uuid.UUID
    scopes: list[str] | None
    created_at: str


class ApiKeyListItem(BaseModel):
    """Safe representation — no full key."""
    id: uuid.UUID
    name: str
    key_prefix: str
    project_id: uuid.UUID
    scopes: list[str] | None
    is_active: bool
    last_used_at: str | None
    created_at: str
    model_config = {"from_attributes": True}


class RenameApiKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


# ---------------------------------------------------------------------------
# Key generation helpers
# ---------------------------------------------------------------------------

def _generate_api_key() -> str:
    """Generate a cryptographically secure 40-byte hex API key."""
    return "asep_" + os.urandom(40).hex()


def _hash_key(full_key: str) -> str:
    """Return the SHA-256 hex digest of the full API key."""
    return hashlib.sha256(full_key.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: CreateApiKeyRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> ApiKeyCreatedResponse:
    """Generate a new API key for a project. The full key is returned ONCE."""
    # Verify project belongs to user's org
    result = await db.execute(select(Project).where(Project.id == payload.project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if current_user.org_id and project.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project does not belong to your organization.")

    full_key = _generate_api_key()
    key_hash = _hash_key(full_key)
    key_prefix = full_key[:12]  # "asep_" + first 7 chars of hex

    api_key = ApiKey(
        id=uuid.uuid4(),
        project_id=payload.project_id,
        user_id=current_user.id,
        name=payload.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=payload.scopes,
        is_active=True,
    )
    db.add(api_key)
    await db.flush()
    await db.refresh(api_key)

    logger.info(
        "API key created",
        extra={"key_id": str(api_key.id), "project_id": str(payload.project_id)},
    )

    return ApiKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=key_prefix,
        full_key=full_key,   # Only time the full key is returned
        project_id=api_key.project_id,
        scopes=api_key.scopes,
        created_at=api_key.created_at.isoformat(),
    )


@router.get("", response_model=list[ApiKeyListItem])
async def list_api_keys(
    current_user: CurrentUser,
    db: DbSession,
    project_id: uuid.UUID | None = None,
) -> list[ApiKeyListItem]:
    """List API keys for the current user (optionally filtered by project)."""
    stmt = select(ApiKey).where(ApiKey.user_id == current_user.id)
    if project_id:
        stmt = stmt.where(ApiKey.project_id == project_id)
    stmt = stmt.order_by(ApiKey.created_at.desc()).limit(100)
    result = await db.execute(stmt)
    keys = list(result.scalars().all())

    return [
        ApiKeyListItem(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            project_id=k.project_id,
            scopes=k.scopes,
            is_active=k.is_active,
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            created_at=k.created_at.isoformat(),
        )
        for k in keys
    ]


@router.delete("/{key_id}", status_code=status.HTTP_200_OK)
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """Revoke an API key (soft-delete: row kept for audit)."""
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found.")
    key.is_active = False
    await db.flush()
    logger.info("API key revoked", extra={"key_id": str(key_id)})
    return {"detail": "API key revoked successfully."}


@router.patch("/{key_id}", response_model=ApiKeyListItem)
async def rename_api_key(
    key_id: uuid.UUID,
    payload: RenameApiKeyRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> ApiKeyListItem:
    """Rename an API key."""
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found.")
    key.name = payload.name
    await db.flush()
    await db.refresh(key)
    return ApiKeyListItem(
        id=key.id,
        name=key.name,
        key_prefix=key.key_prefix,
        project_id=key.project_id,
        scopes=key.scopes,
        is_active=key.is_active,
        last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
        created_at=key.created_at.isoformat(),
    )
