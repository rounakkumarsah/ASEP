"""
ASEP — Production Health Check
"""

import logging
from src.production.compatibility import CompatibilityChecker

logger = logging.getLogger(__name__)


async def production_health_check() -> bool:
    """Verifies that the production readiness tools are functional."""
    try:
        is_compatible = CompatibilityChecker.validate_startup()
        if not is_compatible:
            logger.warning("Production health check failed: modules incompatible")
            return False

        logger.info("Production health check passed")
        return True
    except Exception as exc:
        logger.warning(f"Production health check failed: {exc}")
        return False
