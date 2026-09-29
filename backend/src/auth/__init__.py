"""
ASEP — Authentication Package
"""

def __getattr__(name: str):
    if name in ("CurrentUser", "get_current_user"):
        from .dependencies import CurrentUser, get_current_user
        if name == "CurrentUser":
            return CurrentUser
        return get_current_user
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["CurrentUser", "get_current_user"]
