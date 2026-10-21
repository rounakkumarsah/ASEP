"""
ASEP — Key Vault Encryption Utility (BYOK)
===========================================
Provides Fernet-based symmetric encryption and decryption for user API keys at rest.
"""

from __future__ import annotations

import base64
import hashlib
import os
from typing import Any

from cryptography.fernet import Fernet
import structlog

from src.config.settings import get_settings

logger = structlog.get_logger(__name__)

_fernet_instance: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance

    secret = os.environ.get("ASEP_KEY_VAULT_SECRET", "").strip()
    if not secret:
        try:
            settings = get_settings()
            secret = getattr(settings, "ASEP_KEY_VAULT_SECRET", "") or ""
            secret = secret.strip() if secret else ""
        except Exception:
            secret = ""

    if not secret:
        logger.warning("key_vault_secret_missing")
        settings = get_settings()
        fallback_source = (
            getattr(settings, "SECRET_KEY", None)
            or getattr(settings, "JWT_SECRET_KEY", None)
            or "asep_default_key_vault_master_fallback_secret"
        ).encode("utf-8")
        derived = base64.urlsafe_b64encode(
            hashlib.sha256(fallback_source + b"asep_key_vault_static_salt_v1").digest()
        )
        _fernet_instance = Fernet(derived)
        return _fernet_instance

    try:
        _fernet_instance = Fernet(secret.encode("utf-8"))
        return _fernet_instance
    except Exception:
        derived = base64.urlsafe_b64encode(
            hashlib.sha256(secret.encode("utf-8") + b"asep_key_vault_static_salt_v1").digest()
        )
        _fernet_instance = Fernet(derived)
        return _fernet_instance


def encrypt_key(raw: str) -> str:
    """Encrypt a raw API key using Fernet."""
    if not raw:
        return ""
    f = _get_fernet()
    encrypted_bytes = f.encrypt(raw.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_key(encrypted: str) -> str:
    """Decrypt a Fernet-encrypted API key."""
    if not encrypted:
        return ""
    f = _get_fernet()
    decrypted_bytes = f.decrypt(encrypted.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")


def mask_key(raw: str) -> str:
    """Generate a masked preview of an API key, e.g. 'sk-...abcd'."""
    if not raw:
        return ""
    cleaned = raw.strip()
    if len(cleaned) <= 8:
        if len(cleaned) <= 4:
            return "****"
        return f"{cleaned[:2]}...{cleaned[-2:]}"

    prefix = cleaned[:3]
    suffix = cleaned[-4:]
    return f"{prefix}...{suffix}"
