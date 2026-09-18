"""
ASEP — Cryptography Utility
===========================
Provides encryption and decryption for sensitive configuration data,
such as MCP environment variables (API tokens, private keys) at rest.
"""

from __future__ import annotations

import base64
import logging
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    _HAS_CRYPTOGRAPHY = True
except ImportError:
    _HAS_CRYPTOGRAPHY = False
    Fernet = None  # type: ignore

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

_fernet_instance: Any = None


def _get_fernet() -> Any:
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance

    if not _HAS_CRYPTOGRAPHY:
        return None

    settings = get_settings()
    master = (
        getattr(settings, "SECRET_KEY", None)
        or getattr(settings, "JWT_SECRET_KEY", None)
        or "asep_default_master_encryption_key_32b_secret"
    ).encode("utf-8")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"asep_mcp_secure_static_salt_v1",
        iterations=100_000,
    )
    derived_key = base64.urlsafe_b64encode(kdf.derive(master))
    _fernet_instance = Fernet(derived_key)
    return _fernet_instance


def encrypt_env_vars(env_dict_or_str: str | dict[str, str]) -> str:
    """Encrypt environment variables text/JSON at rest."""
    import json
    if not env_dict_or_str:
        return ""
    if isinstance(env_dict_or_str, dict):
        raw_text = json.dumps(env_dict_or_str)
    else:
        raw_text = str(env_dict_or_str)

    f = _get_fernet()
    if f is None:
        # Fallback to base64 encoding if cryptography is unavailable
        b64 = base64.b64encode(raw_text.encode("utf-8")).decode("utf-8")
        return "b64:" + b64

    encrypted_bytes = f.encrypt(raw_text.encode("utf-8"))
    return "enc:" + encrypted_bytes.decode("utf-8")


def decrypt_env_vars(encrypted_token: str | None) -> str:
    """Decrypt environment variables token back to raw string."""
    if not encrypted_token:
        return ""
    if encrypted_token.startswith("b64:"):
        try:
            return base64.b64decode(encrypted_token[4:].encode("utf-8")).decode("utf-8")
        except Exception:
            return ""
    if not encrypted_token.startswith("enc:"):
        # Unencrypted legacy string or plaintext
        return encrypted_token

    raw_token = encrypted_token[4:]
    try:
        f = _get_fernet()
        if f is None:
            return ""
        decrypted_bytes = f.decrypt(raw_token.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception as exc:
        logger.error("Failed to decrypt environment variables: %s", exc)
        return ""
