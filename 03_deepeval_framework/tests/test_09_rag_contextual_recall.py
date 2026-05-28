"""Metric #9: ContextualRecallMetric — every fact needed to answer is actually retrieved."""
import pytest
from deepeval.metrics import ContextualRecallMetric
from deepeval.test_case import LLMTestCase


@pytest.mark.rag
@pytest.mark.retrieval
@pytest.mark.slow
@pytest.mark.needs_rag
def test_rag_contextual_recall(rag, rag_alive, rag_goldens, judge):
    assert rag_alive
    metric = ContextualRecallMetric(threshold=0.6, model=judge, include_reason=True)
    failures = []
    for g in rag_goldens:
        result = rag.chat(g.input)
        tc = LLMTestCase(
            input=g.input,
            actual_output=result.answer,
            expected_output=g.expected_output,
            retrieval_context=result.retrieval_context,
        )
        metric.measure(tc)
        if not metric.is_successful():
            failures.append((g.input, metric.score, metric.reason))
    assert not failures, f"Contextual-recall failures: {failures}"
