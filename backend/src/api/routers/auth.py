"""
ASEP — Auth Router
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.dependencies import AuthServiceDep, CurrentUser
from src.auth.schemas import RefreshTokenRequest, RefreshTokenResponse, TokenResponse, UserResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthServiceDep,
) -> TokenResponse:
    """Login and obtain access and refresh tokens."""
    user = await auth_service.authenticate_user(form_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    tokens = auth_service.create_login_tokens(user)
    return TokenResponse(access_token=tokens.access_token)


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh(
    payload: RefreshTokenRequest,
    auth_service: AuthServiceDep,
) -> RefreshTokenResponse:
    """Exchange a refresh token for new access and refresh tokens."""
    try:
        return await auth_service.refresh_tokens(payload.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    """Get the currently authenticated user's profile."""
    return current_user
