"""
ASEP — Users API Router
=======================
Endpoints for operator profiles, username availability checks, and daily quotas.
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from src.auth.dependencies import AuthServiceDep, CurrentUser
from src.auth.schemas import (
    CheckUsernameResponse,
    ProfileUpdateRequest,
    UserQuotaResponse,
    UserResponse,
)
from src.production.monetization import FreemiumRateLimiter

router = APIRouter(prefix="/users", tags=["Users"])
_rate_limiter = FreemiumRateLimiter(free_daily_limit=10)


@router.get("/check-username", response_model=CheckUsernameResponse)
async def check_username_availability(
    username: Annotated[str, Query(..., min_length=1, max_length=50, description="Username to check")],
    auth_service: AuthServiceDep,
) -> CheckUsernameResponse:
    """Check whether a username is valid and available (case-insensitive)."""
    available, suggestions = await auth_service.check_username_availability(username)
    return CheckUsernameResponse(available=available, suggestions=suggestions)


@router.patch("/profile", response_model=UserResponse)
async def update_user_profile(
    data: ProfileUpdateRequest,
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
) -> UserResponse:
    """Update human operator profile (first_name, last_name, username)."""
    try:
        updated = await auth_service.update_user(current_user.id, data)
        return UserResponse.model_validate(updated)
    except ValueError as exc:
        err_str = str(exc)
        if "already taken" in err_str.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_str,
        )


@router.get("/quota", response_model=UserQuotaResponse)
async def get_user_quota(
    current_user: CurrentUser,
) -> UserQuotaResponse:
    """Get current daily AI quota usage without decrementing or consuming credits."""
    user_tier = getattr(current_user, "role", "free") or "free"
    result = await _rate_limiter.get_usage(str(current_user.id), tier=user_tier)
    limit = 10 if user_tier == "free" else 999999
    used = max(0, limit - result.remaining_queries) if user_tier == "free" else 0
    return UserQuotaResponse(
        tier=result.current_tier,
        limit=limit,
        used=used,
        remaining=result.remaining_queries,
        reset_seconds=result.reset_seconds,
    )


@router.get("/me", response_model=UserResponse)
async def get_user_me(
    current_user: CurrentUser,
) -> UserResponse:
    """Get current authenticated user profile."""
    return UserResponse.model_validate(current_user)
