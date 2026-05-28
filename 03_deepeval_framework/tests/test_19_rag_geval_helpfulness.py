"""Metric #20: G-Eval (Helpfulness) on RAG."""
import pytest
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams


@pytest.mark.rag
@pytest.mark.geval
@pytest.mark.slow
@pytest.mark.needs_rag
def test_rag_helpfulness(rag, rag_alive, rag_goldens, judge):
    assert rag_alive
    metric = GEval(
        name="Helpfulness",
        criteria=(
            "Is the actual_output a helpful answer to the input? "
            "It should be specific, actionable, and address the question directly. "
            "Generic refusals to in-scope questions score low."
        ),
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        model=judge,
        threshold=0.6,
    )
    failures = []
    for g in rag_goldens:
        result = rag.chat(g.input)
        tc = LLMTestCase(input=g.input, actual_output=result.answer)
        metric.measure(tc)
        if not metric.is_successful():
            failures.append((g.input, metric.score, metric.reason))
    assert not failures, f"RAG helpfulness failures: {failures}"
