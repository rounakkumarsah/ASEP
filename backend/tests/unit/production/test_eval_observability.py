"""
ASEP — Unit Tests for Evaluation, Observability & Operations (Phase P2)
"""

import pytest

from src.production.eval_framework import EvaluationFramework
from src.production.governance_engine import GovernanceEngine
from src.production.observability_tracer import AgentObservabilityTracer
from src.production.opentelemetry_tracing import OpenTelemetryProvider
from src.production.reliability import CircuitBreaker, CircuitBreakerOpenException, DeadLetterQueue


def test_eval_framework():
    framework = EvaluationFramework()
    res = framework.evaluate_output(
        test_id="t1",
        generated_response="The PostgreSQL database connection string is configured in environment variables.",
        context_sources=["PostgreSQL database connection string environment variables"],
    )
    assert res.passed is True
    assert res.groundedness_score >= 0.5
    assert res.hallucination_detected is False



def test_observability_tracer():
    tracer = AgentObservabilityTracer()
    tracer.start_span("s1", "tr1", "planner", "decompose_task")
    tracer.end_span("s1", status="ok", tokens_used=150, cost_usd=0.0002)

    summary = tracer.get_trace_summary("tr1")
    assert summary["span_count"] == 1
    assert summary["total_tokens"] == 150
    assert summary["total_cost_usd"] == 0.0002


def test_opentelemetry_provider():
    otel = OpenTelemetryProvider()
    cid = otel.create_correlation_id()
    assert cid.startswith("trace-")

    metrics_prom = otel.export_prometheus_metrics({"request_count": 100})
    assert "asep_request_count 100" in metrics_prom


def test_governance_engine():
    gov = GovernanceEngine()
    v = gov.record_violation("v1", "exec-1", "NoHardcodedSecrets", "HIGH", "Secret key found in prompt")
    assert v.severity == "HIGH"

    pv = gov.register_prompt_version("p1", "1.0.0", "System prompt text", "admin")
    assert pv.version == "1.0.0"


def test_circuit_breaker_and_dlq():
    cb = CircuitBreaker("vector_db", failure_threshold=2)
    cb.record_failure()
    cb.record_failure()

    with pytest.raises(CircuitBreakerOpenException):
        cb.check_state()

    dlq = DeadLetterQueue()
    dlq.enqueue("m1", "e1", "planner", {"task": "plan"}, "Timeout")
    assert len(dlq.list_messages()) == 1

    replayed = dlq.replay_message("m1")
    assert replayed.message_id == "m1"
    assert len(dlq.list_messages()) == 0
