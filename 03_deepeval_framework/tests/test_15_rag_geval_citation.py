"""Metric #15: G-Eval (Citation Quality) — does the answer cite source files correctly?"""
import pytest
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams


@pytest.mark.rag
@pytest.mark.geval
@pytest.mark.slow
@pytest.mark.needs_rag
def test_rag_citation_quality(rag, rag_alive, rag_goldens, judge):
    assert rag_alive
    metric = GEval(
        name="CitationQuality",
        criteria=(
            "Score 1.0 if the actual_output cites at least one source filename in square brackets "
            "(e.g. [refund_policy.md]) AND the cited source is one of the items in retrieval_context. "
            "Score 0.0 if no citation is present. Score 0.5 if a citation is present but does not "
            "match any retrieved source."
        ),
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.RETRIEVAL_CONTEXT],
        model=judge,
        threshold=0.5,
    )
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
    assert not failures, f"Citation-quality failures: {failures}"
