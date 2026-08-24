"""
ASEP — Production Diagnostics
"""

import logging

from src.control_plane.control_api import ControlPlaneAPI
from src.production.versioning import SystemVersion

logger = logging.getLogger(__name__)


class DiagnosticsRunner:
    """Aggregates system health and diagnostics."""

    def __init__(self, api: ControlPlaneAPI):
        self.api = api

    def run_diagnostics(self) -> dict:
        """Runs a full diagnostic check on the system."""
        try:
            import psutil  # lazy-loaded — optional system monitoring dependency
            mem = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.1)
            hardware = {
                "cpu_percent": cpu,
                "memory_used_mb": mem.used / (1024 * 1024),
                "memory_percent": mem.percent,
            }
        except ImportError:
            hardware = {"cpu_percent": 0.0, "memory_used_mb": 0.0, "memory_percent": 0.0}

        overview = self.api.dashboard.get_system_overview()

        report = {
            "version": SystemVersion.get_version(),
            "system_health": overview["system_status"],
            "active_sessions": overview["active_sessions_count"],
            "pending_approvals": overview["pending_approvals_count"],
            "hardware": hardware,
        }

        if report["hardware"]["memory_percent"] > 90:
            logger.warning("High memory usage detected!")

        return report
