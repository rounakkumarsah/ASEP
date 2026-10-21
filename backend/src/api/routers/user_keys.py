"""
ASEP — User API Keys (BYOK) Router
===================================
Endpoints for managing user-scoped Bring Your Own Key credentials for LLM providers.
"""

from __future__ import annotations

import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.auth.dependencies import CurrentUser
from src.auth.key_vault import decrypt_key, encrypt_key, mask_key
from src.licensing.license_manager import require_license
from src.db.postgres import DbSession
from src.db.repositories.user_api_key_repository import (
    create_or_update,
    delete,
    get_all_for_user,
    get_by_user_and_provider,
    mark_invalid,
)
from src.services.key_validator import validate_provider_key

router = APIRouter(prefix="/api/v1/user-keys", tags=["user-keys"])

SUPPORTED_PROVIDERS = {"groq", "gemini", "openrouter", "openai", "anthropic"}


class AddUserKeyRequest(BaseModel):
    provider: str = Field(..., description="Provider identifier (groq, gemini, openrouter, openai, anthropic)")
    api_key: str = Field(..., description="Raw provider API key to store")


class UserKeyResponse(BaseModel):
    provider: str
    key_preview: str
    is_valid: bool
    last_validated_at: datetime.datetime | None = None
    last_error: str | None = None


class ValidateKeyResponse(BaseModel):
    is_valid: bool
    last_error: str | None = None
    last_validated_at: datetime.datetime | None = None


class DeleteKeyResponse(BaseModel):
    deleted: bool


@router.post("", response_model=UserKeyResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(require_license)])
@router.post("/", response_model=UserKeyResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(require_license)])
async def add_or_update_key(
    body: AddUserKeyRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> UserKeyResponse:
    provider = body.provider.lower().strip()
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider '{provider}'. Must be one of: {', '.join(sorted(SUPPORTED_PROVIDERS))}",
        )

    raw_key = body.api_key.strip()
    if not raw_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key cannot be empty",
        )

    is_valid, reason = await validate_provider_key(provider, raw_key)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason or "invalid_key",
        )

    encrypted = encrypt_key(raw_key)
    preview = mask_key(raw_key)
    key_record = await create_or_update(
        session=db,
        user_id=current_user.id,
        provider=provider,
        encrypted_key=encrypted,
        key_preview=preview,
    )

    return UserKeyResponse(
        provider=key_record.provider,
        key_preview=key_record.key_preview,
        is_valid=key_record.is_valid,
        last_validated_at=key_record.last_validated_at,
        last_error=key_record.last_error,
    )


@router.get("", response_model=list[UserKeyResponse])
@router.get("/", response_model=list[UserKeyResponse])
async def list_keys(
    current_user: CurrentUser,
    db: DbSession,
) -> list[UserKeyResponse]:
    keys = await get_all_for_user(db, current_user.id)
    return [
        UserKeyResponse(
            provider=k.provider,
            key_preview=k.key_preview,
            is_valid=k.is_valid,
            last_validated_at=k.last_validated_at,
            last_error=k.last_error,
        )
        for k in keys
    ]


@router.delete("/{provider}", response_model=DeleteKeyResponse)
async def delete_key(
    provider: str,
    current_user: CurrentUser,
    db: DbSession,
) -> DeleteKeyResponse:
    p = provider.lower().strip()
    await delete(db, current_user.id, p)
    return DeleteKeyResponse(deleted=True)


@router.post("/{provider}/validate", response_model=ValidateKeyResponse)
async def validate_existing_key(
    provider: str,
    current_user: CurrentUser,
    db: DbSession,
) -> ValidateKeyResponse:
    p = provider.lower().strip()
    key_record = await get_by_user_and_provider(db, current_user.id, p)
    if not key_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No key found for provider '{p}'",
        )

    try:
        raw_key = decrypt_key(key_record.encrypted_key)
    except Exception:
        await mark_invalid(db, current_user.id, p, "decryption_failed")
        return ValidateKeyResponse(
            is_valid=False,
            last_error="decryption_failed",
            last_validated_at=key_record.last_validated_at,
        )

    is_valid, reason = await validate_provider_key(p, raw_key)
    now = datetime.datetime.now(datetime.timezone.utc)
    if is_valid:
        key_record.is_valid = True
        key_record.last_error = None
        key_record.last_validated_at = now
        await db.flush()
    else:
        await mark_invalid(db, current_user.id, p, reason or "invalid_key")
        key_record.is_valid = False
        key_record.last_error = reason or "invalid_key"
        key_record.last_validated_at = now
        await db.flush()

    return ValidateKeyResponse(
        is_valid=key_record.is_valid,
        last_error=key_record.last_error,
        last_validated_at=key_record.last_validated_at,
    )
