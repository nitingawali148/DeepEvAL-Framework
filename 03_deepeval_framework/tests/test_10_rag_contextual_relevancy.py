"""Metric #10: ContextualRelevancyMetric — most retrieved chunks are on-topic."""
import pytest
from deepeval.metrics import ContextualRelevancyMetric
from deepeval.test_case import LLMTestCase


@pytest.mark.rag
@pytest.mark.retrieval
@pytest.mark.slow
@pytest.mark.needs_rag
def test_rag_contextual_relevancy(rag, rag_alive, rag_goldens, judge):
    assert rag_alive
    metric = ContextualRelevancyMetric(threshold=0.6, model=judge, include_reason=True)
    failures = []
    for g in rag_goldens:
        result = rag.chat(g.input)
        tc = LLMTestCase(
            input=g.input,
            actual_output=result.answer,
            retrieval_context=result.retrieval_context,
        )
        metric.measure(tc)
        if not metric.is_successful():
            failures.append((g.input, metric.score, metric.reason))
    assert not failures, f"Contextual-relevancy failures: {failures}"
