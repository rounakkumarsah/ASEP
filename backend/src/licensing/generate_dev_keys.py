import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def generate_dev_keys() -> str:
    """Generate RSA key pair and dev license token."""
    base_dir = Path(__file__).resolve().parent
    repo_root = base_dir.parent.parent
    workspace_parent = repo_root.parent

    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = private.public_key()

    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    priv_pem = private.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    with open(base_dir / "public_key.pem", "wb") as f:
        f.write(pub_pem)

    with open(workspace_parent / "asep_private_key.pem", "wb") as f:
        f.write(priv_pem)

    header = {"alg": "RS256", "typ": "JWT"}
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "asep-license",
        "customer": "dev-test",
        "tier": "pro",
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(days=30)).isoformat(),
        "features": ["byok", "reranker", "injection_classifier"],
        "max_users": 10,
    }

    h = b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p = b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    msg = f"{h}.{p}".encode("utf-8")
    sig = private.sign(msg, padding.PKCS1v15(), hashes.SHA256())
    token = f"{h}.{p}.{b64url(sig)}"

    with open(repo_root / "generated_license.txt", "w", encoding="utf-8") as f:
        f.write(token)

    return token


if __name__ == "__main__":
    generate_dev_keys()
