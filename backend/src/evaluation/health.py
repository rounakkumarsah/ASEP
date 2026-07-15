"""
ASEP — Evaluation Health Check
"""

import logging

from src.evaluation.datasets import SAMPLE_DATASET
from src.evaluation.scoring import Scorer
from src.evaluation.tracing import Trace, TraceStore, Tracer
from src.evaluation.trajectory import TrajectoryAnalyzer

logger = logging.getLogger(__name__)


async def evaluation_health_check() -> bool:
    """Verifies evaluation components instantiate and produce valid typed outputs.

    Returns:
        True if all components initialise and produce expected outputs.
    """
    try:
        # 1. Dataset constant is accessible
        assert len(SAMPLE_DATASET.cases) >= 3, "SAMPLE_DATASET must have at least 3 cases"
        for case in SAMPLE_DATASET.cases:
            assert 0.0 <= case.pass_threshold <= 1.0

        # 2. Tracer lifecycle
        trace = Trace(trace_id="hc-trace", session_id="hc", thread_id="hc", run_id="hc-run")
        tracer = Tracer(trace)
        async with tracer.span("health_check_span", test=True) as span:
            assert span.name == "health_check_span"
        assert len(trace.spans) == 1

        store = TraceStore()
        store.add(trace)
        assert store.get("hc-trace") is not None

        # 3. TrajectoryAnalyzer produces valid analysis with empty input
        analyzer = TrajectoryAnalyzer()
        from src.evaluation.trajectory import Trajectory
        traj = Trajectory(session_id="hc", thread_id="hc", run_id="hc-run", trace_id="hc-trace")
        analysis = analyzer.analyze(traj)
        assert analysis.path_efficiency_ratio == 0.0

        # 4. Scorer produces bounded output
        scorer = Scorer()
        from src.evaluation.metrics import LatencyMetrics, SessionMetrics, MemoryMetrics
        metrics = SessionMetrics(
            session_id="hc", run_id="hc-run", thread_id="hc", trace_id="hc-trace",
            task_count=2, succeeded=2,
        )
        exec_score = scorer.score_execution(metrics)
        assert 0.0 <= exec_score.score <= 1.0

        lat = LatencyMetrics(total_ms=3000.0, planning_ms=500.0, execution_ms=2500.0)
        lat_score = scorer.score_latency(lat)
        assert lat_score.grade == "excellent"

        logger.info("Evaluation health check passed")
        return True

    except Exception as exc:
        logger.warning(f"Evaluation health check failed: {exc}")
        return False
