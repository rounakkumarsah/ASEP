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
        if required_major != cls.MAJOR:
            return False
        return required_minor <= cls.MINOR
