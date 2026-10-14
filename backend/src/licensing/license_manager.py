"""
ASEP — Offline-Verifiable License Manager
=========================================
Protects ASEP from unauthorized resale using offline-verifiable RS256 JWT licenses.
"""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from fastapi import HTTPException
import structlog

logger = structlog.get_logger(__name__)

_PUBLIC_KEY_PATH = Path(__file__).parent / "public_key.pem"


def _b64url_decode(data: str) -> bytes:
    """Decode base64url-encoded string."""
    rem = len(data) % 4
    if rem > 0:
        data += "=" * (4 - rem)
    return base64.urlsafe_b64decode(data.encode("utf-8"))


class LicenseManager:
    """Offline-verifiable license manager."""

    def __init__(self, public_key_path: Path | str | None = None) -> None:
        self._public_key_path = Path(public_key_path) if public_key_path else _PUBLIC_KEY_PATH
        self._public_key: Any = None
        self._license_info: dict[str, Any] = {}
        self._is_licensed: bool = False
        self._last_verified_at: datetime | None = None
        self._load_and_verify()

    def _load_public_key(self) -> Any:
        if self._public_key is not None:
            return self._public_key

        if not self._public_key_path.exists():
            logger.critical("license_public_key_missing", path=str(self._public_key_path))
            return None
        try:
            with open(self._public_key_path, "rb") as f:
                content = f.read()
            self._public_key = serialization.load_pem_public_key(content)
            return self._public_key
        except Exception as exc:
            logger.critical("license_public_key_invalid", error=str(exc))
            return None

    def _load_and_verify(self, explicit_key: str | None = None) -> None:
        if explicit_key is not None:
            license_key = explicit_key
        elif "ASEP_LICENSE_KEY" in os.environ:
            license_key = os.environ.get("ASEP_LICENSE_KEY")
        else:
            # Fallback: attempt reading from .env file if environment variable not yet loaded
            try:
                from dotenv import load_dotenv
                backend_env = Path(__file__).resolve().parent.parent.parent / ".env"
                if backend_env.exists():
                    load_dotenv(backend_env)
                else:
                    load_dotenv()
                license_key = os.environ.get("ASEP_LICENSE_KEY")
            except Exception:
                pass

        if not license_key:
            logger.critical("license_invalid", reason="missing_license_key")
            self._is_licensed = False
            self._license_info = {}
            return

        valid, info_or_reason = self._verify_token(license_key)
        if valid and isinstance(info_or_reason, dict):
            self._is_licensed = True
            self._license_info = info_or_reason
            self._last_verified_at = datetime.now(timezone.utc)
            logger.info("license_verified", customer=info_or_reason.get("customer"), tier=info_or_reason.get("tier"))
        else:
            self._is_licensed = False
            self._license_info = {}
            logger.critical("license_invalid", reason=str(info_or_reason))

    def _verify_token(self, token: str) -> tuple[bool, dict[str, Any] | str]:
        parts = token.strip().split(".")
        if len(parts) != 3:
            return False, "invalid_jwt_format"

        header_b64, payload_b64, sig_b64 = parts
        try:
            header = json.loads(_b64url_decode(header_b64).decode("utf-8"))
            payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
            signature = _b64url_decode(sig_b64)
        except Exception as exc:
            return False, f"decode_error: {exc}"

        if header.get("alg") != "RS256":
            return False, f"unsupported_algorithm: {header.get('alg')}"

        if payload.get("sub") != "asep-license":
            return False, f"invalid_subject: {payload.get('sub')}"

        public_key = self._load_public_key()
        if public_key is None:
            return False, "public_key_unavailable"

        # Verify cryptographic signature
        signed_message = f"{header_b64}.{payload_b64}".encode("utf-8")
        try:
            public_key.verify(
                signature,
                signed_message,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        except InvalidSignature:
            return False, "signature_verification_failed"
        except Exception as exc:
            return False, f"crypto_error: {exc}"

        # Verify validity window (issued_at and expires_at)
        now = datetime.now(timezone.utc)

        issued_at_str = payload.get("issued_at")
        if issued_at_str:
            try:
                issued_at = datetime.fromisoformat(issued_at_str.replace("Z", "+00:00"))
                if issued_at.tzinfo is None:
                    issued_at = issued_at.replace(tzinfo=timezone.utc)
                from datetime import timedelta
                if now < (issued_at - timedelta(minutes=5)):
                    return False, f"license_not_yet_valid: {issued_at_str}"
            except Exception as exc:
                return False, f"invalid_issued_at_format: {exc}"

        expires_at_str = payload.get("expires_at")
        if not expires_at_str:
            return False, "missing_expires_at"

        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if now > expires_at:
                return False, f"license_expired: {expires_at_str}"
        except Exception as exc:
            return False, f"invalid_expires_at_format: {exc}"

        return True, payload

    def is_licensed(self) -> bool:
        """Return True if currently active license is valid and unexpired."""
        if not self._is_licensed:
            return False
        return self.heartbeat()

    def get_license_info(self) -> dict[str, Any]:
        """Return decrypted/verified license metadata payload."""
        return dict(self._license_info)

    def activate(self, license_key: str) -> tuple[bool, str | None]:
        """Activate a new license key in-memory and update runtime status."""
        valid, info_or_reason = self._verify_token(license_key)
        if valid and isinstance(info_or_reason, dict):
            self._is_licensed = True
            self._license_info = info_or_reason
            self._last_verified_at = datetime.now(timezone.utc)
            os.environ["ASEP_LICENSE_KEY"] = license_key
            logger.info("license_activated", customer=info_or_reason.get("customer"), tier=info_or_reason.get("tier"))
            return True, None
        else:
            self._is_licensed = False
            self._license_info = {}
            logger.critical("license_activation_failed", reason=str(info_or_reason))
            return False, str(info_or_reason)

    def heartbeat(self) -> bool:
        """Offline heartbeat checking whether current time remains valid."""
        if not self._is_licensed or not self._license_info:
            return False
        expires_at_str = self._license_info.get("expires_at")
        if not expires_at_str:
            return False
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc) <= expires_at
        except Exception:
            return False


# Global singleton instance
_GLOBAL_LICENSE_MANAGER: LicenseManager | None = None


def get_license_manager() -> LicenseManager:
    """Return the global LicenseManager instance."""
    global _GLOBAL_LICENSE_MANAGER
    if _GLOBAL_LICENSE_MANAGER is None:
        _GLOBAL_LICENSE_MANAGER = LicenseManager()
    return _GLOBAL_LICENSE_MANAGER


async def require_license() -> None:
    """
    FastAPI dependency ensuring valid license before accessing protected endpoints.
    Raises HTTP 402 Payment Required if license is missing or invalid.
    """
    lm = get_license_manager()
    if not lm.is_licensed():
        raise HTTPException(
            status_code=402,
            detail="License required. Set ASEP_LICENSE_KEY in .env.",
        )
