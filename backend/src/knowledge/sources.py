"""
ASEP — Knowledge Source Registry
"""

import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KnowledgeSource(BaseModel):
    """Configuration definition for a trusted knowledge sync source."""
    source_id: str
    name: str
    source_type: str  # Git Repository, Documentation, Local Files, Markdown, PDF, HTML, API, Website
    source_url: Optional[str] = None
    version: str = "1.0"
    is_enabled: bool = True
    trust_level: float = Field(default=0.8, ge=0.0, le=1.0)
    license: Optional[str] = "Proprietary"
    language: str = "en"
    provenance: str = "System Config"


class SourceRegistry:
    """Thread-safe registry for configuring sync sources."""

    def __init__(self) -> None:
        self._sources: Dict[str, KnowledgeSource] = {}

    def register_source(self, source: KnowledgeSource) -> None:
        """Register a knowledge source."""
        self._sources[source.source_id] = source
        logger.info(f"Registered knowledge source: {source.source_id} ({source.source_type})")

    def unregister_source(self, source_id: str) -> None:
        """Unregister a knowledge source."""
        if source_id in self._sources:
            del self._sources[source_id]
            logger.info(f"Unregistered knowledge source: {source_id}")

    def discover_sources(self) -> List[KnowledgeSource]:
        """Discover all configured knowledge sources."""
        return list(self._sources.values())

    def lookup(self, source_id: str) -> Optional[KnowledgeSource]:
        """Lookup source details by ID."""
        return self._sources.get(source_id)

    def enable_source(self, source_id: str) -> None:
        """Enable a knowledge source."""
        if source_id in self._sources:
            self._sources[source_id].is_enabled = True

    def disable_source(self, source_id: str) -> None:
        """Disable a knowledge source."""
        if source_id in self._sources:
            self._sources[source_id].is_enabled = False

    def metadata(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get source metadata."""
        src = self._sources.get(source_id)
        if not src:
            return None
        return src.model_dump()

    def version(self, source_id: str) -> Optional[str]:
        """Get source version."""
        src = self._sources.get(source_id)
        return src.version if src else None


_global_source_registry: Optional[SourceRegistry] = None

def get_source_registry() -> SourceRegistry:
    global _global_source_registry
    if _global_source_registry is None:
        _global_source_registry = SourceRegistry()
        # Seed basic default source
        _global_source_registry.register_source(KnowledgeSource(
            source_id="default_docs",
            name="ASEP Core Architecture Docs",
            source_type="Documentation",
            source_url="https://asep.internal/docs",
            version="1.2.0"
        ))
    return _global_source_registry
