"""
ASEP — Cross-Module Compatibility
"""

import logging
from src.production.versioning import SystemVersion

logger = logging.getLogger(__name__)


class CompatibilityChecker:
    """Validates module versions against a compatibility manifest."""

    MANIFEST = {
        "memory": {"min_major": 2, "min_minor": 0},
        "evaluator": {"min_major": 2, "min_minor": 0},
        "governance": {"min_major": 2, "min_minor": 2},
        "control_plane": {"min_major": 2, "min_minor": 3},
    }

    @classmethod
    def validate_startup(cls) -> bool:
        """Validates that current system version satisfies module requirements."""
        is_valid = True
        for module, req in cls.MANIFEST.items():
            if not SystemVersion.is_compatible(req["min_major"], req["min_minor"]):
                logger.error(
                    f"Compatibility check failed for {module}: "
                    f"requires {req['min_major']}.{req['min_minor']}, "
                    f"found {SystemVersion.get_version()}"
                )
                is_valid = False
        
        if is_valid:
            logger.info("Startup compatibility check passed for all modules.")
        return is_valid
