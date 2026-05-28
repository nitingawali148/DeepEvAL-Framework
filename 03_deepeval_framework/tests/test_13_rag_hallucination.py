"""Metric #13: RAG Hallucination — uses the expected_output as ground-truth context."""
import pytest
from deepeval.metrics import HallucinationMetric
from deepeval.test_case import LLMTestCase


@pytest.mark.rag
@pytest.mark.quality
@pytest.mark.slow
@pytest.mark.needs_rag
def test_rag_hallucination(rag, rag_alive, rag_goldens, judge):
    assert rag_alive
    metric = HallucinationMetric(threshold=0.4, model=judge, include_reason=True)
    failures = []
    for g in rag_goldens:
        result = rag.chat(g.input)
        tc = LLMTestCase(
            input=g.input,
            actual_output=result.answer,
            context=[g.expected_output],
        )
        metric.measure(tc)
        if not metric.is_successful():
            failures.append((g.input, metric.score, metric.reason))
    assert not failures, f"RAG hallucination failures: {failures}"
