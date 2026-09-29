"""
ASEP — Authentication Utilities
"""


def normalize_email(email: str | None) -> str:
    """Normalize email address: trim, lowercase, and handle Gmail dot/plus normalization."""
    if not email or not isinstance(email, str):
        return ""
    clean = email.strip().lower()
    parts = clean.split("@")
    if len(parts) == 2:
        local_part, domain = parts[0], parts[1]
        if domain in ["gmail.com", "googlemail.com"]:
            # Remove dots and plus-tags for Gmail domain
            local_part = local_part.split("+")[0].replace(".", "")
            return f"{local_part}@{domain}"
    return clean

