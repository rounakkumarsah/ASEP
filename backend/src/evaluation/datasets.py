"""
ASEP — Evaluation Dataset Definitions

Datasets are declared as Python constants in this phase.
JSON/YAML loader support is reserved for a future phase.
"""

from pydantic import BaseModel, Field


class EvaluationCase(BaseModel):
    """A single evaluation scenario with its expectations and pass threshold."""
    id: str
    goal: str
    tags: list[str] = Field(default_factory=list)
    expected_min_tasks: int | None = None
    expected_tool_names: list[str] = Field(default_factory=list)
    pass_threshold: float = Field(default=0.6, ge=0.0, le=1.0)


class EvaluationDataset(BaseModel):
    """A named, versioned collection of evaluation cases."""
    name: str
    version: str = "1.0"
    description: str = ""
    dataset_type: str = "custom"  # golden, benchmark, regression, synthetic, custom
    cases: list[EvaluationCase] = Field(default_factory=list)

    @property
    def case_ids(self) -> list[str]:
        return [c.id for c in self.cases]

    def get_case(self, case_id: str) -> EvaluationCase | None:
        return next((c for c in self.cases if c.id == case_id), None)

    def filter_by_tag(self, tag: str) -> list[EvaluationCase]:
        return [c for c in self.cases if tag in c.tags]


# ─────────────────────────────────────────────────────────────────────────────
# Built-in sample dataset — used for CI smoke-tests and regression baselines
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_DATASET = EvaluationDataset(
    name="asep_sample",
    version="1.0",
    description="Built-in smoke-test dataset for CI regression validation.",
    cases=[
        EvaluationCase(
            id="case_001_basic_goal",
            goal="Summarise the current system health and produce a status report.",
            tags=["smoke", "health", "basic"],
            expected_min_tasks=1,
            expected_tool_names=["system_info"],
            pass_threshold=0.5,
        ),
        EvaluationCase(
            id="case_002_file_analysis",
            goal="Analyse the source code structure and list the top-level modules.",
            tags=["smoke", "fs", "analysis"],
            expected_min_tasks=2,
            expected_tool_names=["read_local_file"],
            pass_threshold=0.55,
        ),
        EvaluationCase(
            id="case_003_multi_step",
            goal="Fetch system information, read a configuration file, and produce a dependency summary.",
            tags=["smoke", "multi-step", "regression"],
            expected_min_tasks=3,
            expected_tool_names=["system_info", "read_local_file"],
            pass_threshold=0.6,
        ),
    ],
)
