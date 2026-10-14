import json
import os
from pathlib import Path
import pytest
from fastapi import HTTPException

from src.licensing.license_manager import LicenseManager, get_license_manager, require_license


_INITIAL_DEV_TOKEN = os.environ.get("ASEP_LICENSE_KEY", "")


@pytest.fixture
def dev_token() -> str:
    token_file = Path(__file__).resolve().parent.parent.parent.parent / "generated_license.txt"
    if token_file.exists():
        return token_file.read_text(encoding="utf-8").strip()
    return _INITIAL_DEV_TOKEN or os.environ.get("ASEP_LICENSE_KEY", "")


def test_license_system_verification(dev_token: str):
    assert dev_token, "Dev token must be available for tests"
    assert len(dev_token) > 50

    # Test valid license
    os.environ["ASEP_LICENSE_KEY"] = dev_token
    lm = LicenseManager()
    assert lm.is_licensed() is True
    info = lm.get_license_info()
    assert info.get("sub") == "asep-license"
    assert info.get("tier") == "pro"
    assert info.get("customer") == "dev-test"
    assert lm.heartbeat() is True


def test_invalid_license_missing():
    old = os.environ.get("ASEP_LICENSE_KEY")
    try:
        os.environ["ASEP_LICENSE_KEY"] = ""
        lm = LicenseManager()
        assert lm.is_licensed() is False
        assert lm.get_license_info() == {}
    finally:
        if old is not None:
            os.environ["ASEP_LICENSE_KEY"] = old
        else:
            os.environ.pop("ASEP_LICENSE_KEY", None)


def test_invalid_license_corrupted(dev_token: str):
    old = os.environ.get("ASEP_LICENSE_KEY")
    try:
        os.environ["ASEP_LICENSE_KEY"] = "invalid.jwt.token"
        lm = LicenseManager()
        assert lm.is_licensed() is False
        assert lm.get_license_info() == {}

        # Tampered signature
        parts = dev_token.split(".")
        tampered = f"{parts[0]}.{parts[1]}.badsignature123"
        os.environ["ASEP_LICENSE_KEY"] = tampered
        lm_tampered = LicenseManager()
        assert lm_tampered.is_licensed() is False
    finally:
        if old is not None:
            os.environ["ASEP_LICENSE_KEY"] = old


def test_license_activation(dev_token: str):
    lm = LicenseManager()
    success, reason = lm.activate("bad.token.here")
    assert success is False
    assert reason is not None

    success, reason = lm.activate(dev_token)
    assert success is True
    assert reason is None
    assert lm.is_licensed() is True


@pytest.mark.asyncio
async def test_require_license_dependency(dev_token: str):
    lm = get_license_manager()
    lm.activate(dev_token)
    # Should not raise
    await require_license()

    # Now invalidate
    lm._is_licensed = False
    with pytest.raises(HTTPException) as exc_info:
        await require_license()
    assert exc_info.value.status_code == 402
