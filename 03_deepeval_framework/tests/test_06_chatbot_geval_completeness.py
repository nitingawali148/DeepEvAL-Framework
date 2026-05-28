"""Metric #6: G-Eval (Completeness) — does the reply cover all key facts in the expected output?"""
import pytest
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams


@pytest.mark.chatbot
@pytest.mark.geval
@pytest.mark.slow
@pytest.mark.needs_chatbot
def test_chatbot_completeness(chatbot, chatbot_goldens, judge):
    metric = GEval(
        name="Completeness",
        criteria=(
            "Does the actual_output cover ALL key facts from the expected_output? "
            "Penalise missing numbers, timeframes, or named items. Brevity is OK if no key fact is missing."
        ),
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        model=judge,
        threshold=0.6,
    )
    failures = []
    for g in chatbot_goldens:
        if not g.expected_output:
            continue
        reply = chatbot.chat(g.input).reply
        tc = LLMTestCase(
            input=g.input,
            actual_output=reply,
            expected_output=g.expected_output,
        )
        metric.measure(tc)
        if not metric.is_successful():
            failures.append((g.input, metric.score, metric.reason))
    assert not failures, f"Completeness failures: {failures}"
