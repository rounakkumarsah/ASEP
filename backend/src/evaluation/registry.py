"""
ASEP — Evaluation Registry
"""

import logging
from typing import Dict, List, Optional, Any
from src.evaluation.datasets import EvaluationDataset

logger = logging.getLogger(__name__)


class EvaluationRegistry:
    """Thread-safe registry for managing validation datasets and execution benchmark schemas."""

    def __init__(self) -> None:
        self._datasets: Dict[str, EvaluationDataset] = {}

    def register(self, dataset: EvaluationDataset) -> None:
        """Register a validation dataset."""
        self._datasets[dataset.name] = dataset
        logger.info(f"Registered evaluation dataset: {dataset.name} (v{dataset.version})")

    def unregister(self, name: str) -> None:
        """Unregister an evaluation dataset."""
        if name in self._datasets:
            del self._datasets[name]
            logger.info(f"Unregistered evaluation dataset: {name}")

    def discover(self) -> List[EvaluationDataset]:
        """Discover all registered evaluation datasets."""
        return list(self._datasets.values())

    def lookup(self, name: str) -> Optional[EvaluationDataset]:
        """Lookup dataset details by unique name key."""
        return self._datasets.get(name)

    def version(self, name: str) -> Optional[str]:
        """Get version of a registered dataset."""
        ds = self.lookup(name)
        return ds.version if ds else None

    def metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata details of a dataset."""
        ds = self.lookup(name)
        if not ds:
            return None
        return {
            "name": ds.name,
            "version": ds.version,
            "description": ds.description,
            "dataset_type": ds.dataset_type,
            "case_count": len(ds.cases)
        }


_global_evaluation_registry: Optional[EvaluationRegistry] = None

def get_evaluation_registry() -> EvaluationRegistry:
    global _global_evaluation_registry
    if _global_evaluation_registry is None:
        _global_evaluation_registry = EvaluationRegistry()
        from src.evaluation.datasets import SAMPLE_DATASET
        _global_evaluation_registry.register(SAMPLE_DATASET)
    return _global_evaluation_registry
