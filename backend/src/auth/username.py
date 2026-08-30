import re

def validate_username(username: str) -> tuple[bool, str, str]:
    """
    Normalizes and validates a username.
    Returns: (is_valid, normalized_username, error_message)
    """
    if not username:
        return False, "", "Username cannot be empty."

    # 1. Normalize: trim spaces and lowercase
    normalized = username.strip().lower()

    # 2. Check for spaces
    if ' ' in normalized:
        return False, normalized, "Username cannot contain spaces."

    # 3. Check length
    if len(normalized) < 3 or len(normalized) > 30:
        return False, normalized, "Username must be between 3 and 30 characters."

    # 4. Check allowed characters (a-z, 0-9, _, .)
    if not re.match(r'^[a-z0-9_.]+$', normalized):
        return False, normalized, "Username can only contain letters, numbers, underscores, and periods."

    return True, normalized, "Username is valid."