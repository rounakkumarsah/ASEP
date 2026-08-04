"""
ASEP — OAuth Provider Integrations
=====================================
Implements GitHub and Google OAuth 2.0 authorization code flow.

Security guarantees:
  - Client secrets are read exclusively from environment settings.
  - State parameter (CSRF protection) is validated against Redis.
  - No secrets are logged or returned to the frontend.
  - All HTTP calls use explicit timeouts to prevent hanging connections.
"""

from __future__ import annotations

import logging
import urllib.parse
from dataclasses import dataclass

import httpx

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_USER_URL = "https://api.github.com/user"
_GITHUB_EMAIL_URL = "https://api.github.com/user/emails"

_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USER_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

_HTTP_TIMEOUT = 10.0  # seconds


@dataclass
class OAuthProfile:
    """Normalized OAuth user profile returned by any provider."""

    provider: str          # "github" or "google"
    oauth_id: str          # provider's user ID (always a string)
    email: str
    name: str | None       # display name (may be None)
    avatar_url: str | None
    email_verified: bool


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------


def build_github_auth_url(state: str) -> str:
    """Build the GitHub OAuth authorization URL with CSRF state parameter.

    Args:
        state: CSRF state token (stored in Redis before redirect).

    Returns:
        Fully-qualified GitHub authorization URL.

    Raises:
        RuntimeError: If GITHUB_CLIENT_ID is not configured.
    """
    settings = get_settings()
    if not settings.GITHUB_CLIENT_ID:
        raise RuntimeError(
            "GITHUB_CLIENT_ID is not configured. "
            "Add it to your .env file to enable GitHub OAuth."
        )
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope": "read:user user:email",
        "state": state,
    }
    return "https://github.com/login/oauth/authorize?" + urllib.parse.urlencode(params)


async def exchange_github_code(code: str) -> OAuthProfile:
    """Exchange a GitHub authorization code for a normalized OAuthProfile.

    Args:
        code: Authorization code returned by GitHub after user consent.

    Returns:
        OAuthProfile with provider="github".

    Raises:
        ValueError: If the token exchange or profile fetch fails.
    """
    settings = get_settings()
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise ValueError("GitHub OAuth credentials are not configured.")

    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
        # Step 1: Exchange code for access token
        token_resp = await client.post(
            _GITHUB_TOKEN_URL,
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()

        access_token = token_data.get("access_token")
        if not access_token:
            error = token_data.get("error_description", token_data.get("error", "unknown"))
            raise ValueError(f"GitHub token exchange failed: {error}")

        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # Step 2: Fetch user profile
        user_resp = await client.get(_GITHUB_USER_URL, headers=auth_headers)
        user_resp.raise_for_status()
        user_data = user_resp.json()

        # Step 3: Fetch verified emails (GitHub may hide primary email)
        email: str | None = user_data.get("email")
        email_verified = False

        email_resp = await client.get(_GITHUB_EMAIL_URL, headers=auth_headers)
        if email_resp.status_code == 200:
            emails = email_resp.json()
            # Prefer verified primary email
            for e in emails:
                if e.get("primary") and e.get("verified"):
                    email = e["email"]
                    email_verified = True
                    break
            # Fallback: any verified email
            if not email_verified:
                for e in emails:
                    if e.get("verified"):
                        email = e["email"]
                        email_verified = True
                        break

        if not email:
            raise ValueError(
                "GitHub account does not have a public or verified email address. "
                "Please add a verified email to your GitHub account and try again."
            )

        name = user_data.get("name") or user_data.get("login")
        avatar_url = user_data.get("avatar_url")

        logger.info(
            "GitHub OAuth profile fetched",
            extra={"github_id": str(user_data["id"]), "email_verified": email_verified},
        )

        return OAuthProfile(
            provider="github",
            oauth_id=str(user_data["id"]),
            email=email.lower().strip(),
            name=name,
            avatar_url=avatar_url,
            email_verified=email_verified,
        )


# ---------------------------------------------------------------------------
# Google
# ---------------------------------------------------------------------------


def build_google_auth_url(state: str) -> str:
    """Build the Google OAuth 2.0 authorization URL with CSRF state parameter.

    Args:
        state: CSRF state token (stored in Redis before redirect).

    Returns:
        Fully-qualified Google authorization URL.

    Raises:
        RuntimeError: If GOOGLE_CLIENT_ID is not configured.
    """
    settings = get_settings()
    if not settings.GOOGLE_CLIENT_ID:
        raise RuntimeError(
            "GOOGLE_CLIENT_ID is not configured. "
            "Add it to your .env file to enable Google OAuth."
        )
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)


async def exchange_google_code(code: str) -> OAuthProfile:
    """Exchange a Google authorization code for a normalized OAuthProfile.

    Args:
        code: Authorization code returned by Google after user consent.

    Returns:
        OAuthProfile with provider="google".

    Raises:
        ValueError: If the token exchange or profile fetch fails.
    """
    settings = get_settings()
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise ValueError("Google OAuth credentials are not configured.")

    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
        # Step 1: Exchange code for tokens
        token_resp = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()

        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("Google token exchange failed: no access_token in response.")

        # Step 2: Fetch user info
        user_resp = await client.get(
            _GOOGLE_USER_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_resp.raise_for_status()
        user_data = user_resp.json()

        email = user_data.get("email")
        if not email:
            raise ValueError("Google account does not have an email address.")

        logger.info(
            "Google OAuth profile fetched",
            extra={"google_id": user_data.get("id"), "verified": user_data.get("verified_email")},
        )

        return OAuthProfile(
            provider="google",
            oauth_id=str(user_data["id"]),
            email=email.lower().strip(),
            name=user_data.get("name"),
            avatar_url=user_data.get("picture"),
            email_verified=bool(user_data.get("verified_email", False)),
        )
