"""
ASEP — Production Versioning
"""

class SystemVersion:
    """Tracks the core version of ASEP."""
    MAJOR = 2
    MINOR = 4
    PATCH = 0

    @classmethod
    def get_version(cls) -> str:
        return f"{cls.MAJOR}.{cls.MINOR}.{cls.PATCH}"

    @classmethod
    def is_compatible(cls, required_major: int, required_minor: int) -> bool:
        if cls.MAJOR != required_major:
            return False
        return cls.MINOR >= required_minor
