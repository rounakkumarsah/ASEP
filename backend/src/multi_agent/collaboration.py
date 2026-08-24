"""
ASEP — Multi-Agent Collaboration & Shared State Engine
======================================================
Provides thread-safe shared state context and consensus workflow management.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SharedStateContext:
    """Thread-safe state memory shared across all agents in an execution session."""

    session_id: str
    _data: dict[str, Any] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def get(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            return self._data.get(key, default)

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._data[key] = value

    async def snapshot(self) -> dict[str, Any]:
        async with self._lock:
            return dict(self._data)


class ConsensusWorkflow:
    """Resolves conflicts and reaches consensus across multi-agent proposals."""

    def resolve_consensus(self, proposals: list[dict[str, Any]]) -> dict[str, Any]:
        if not proposals:
            return {"status": "rejected", "reason": "No proposals provided"}

        # Majority vote on approval
        approvals = [p for p in proposals if p.get("approved", False)]
        is_consensus = len(approvals) >= (len(proposals) / 2.0)

        logger.info(
            "Consensus workflow evaluated: %d/%d approvals -> consensus=%s",
            len(approvals),
            len(proposals),
            is_consensus,
        )

        return {
            "status": "approved" if is_consensus else "rejected",
            "approval_ratio": len(approvals) / len(proposals),
            "winning_proposal": approvals[0] if approvals else proposals[0],
        }
