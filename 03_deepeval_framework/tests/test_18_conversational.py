"""Metric #19: Multi-turn conversational relevancy — does the chatbot stay coherent across turns?"""
import pytest
from deepeval.metrics import ConversationCompletenessMetric
from deepeval.test_case import ConversationalTestCase, LLMTestCase


CONVERSATIONS = [
    [
        ("Hi, I'd like to return an item.", None),
        ("It's a hoodie I bought 25 days ago.", None),
        ("Will I get a refund or store credit?", None),
    ],
    [
        ("What earbuds do you sell?", None),
        ("How long is the battery life?", None),
        ("Are they water resistant?", None),
    ],
]


@pytest.mark.chatbot
@pytest.mark.conversational
@pytest.mark.slow
@pytest.mark.needs_chatbot
def test_conversational_relevancy(chatbot, judge):
    metric = ConversationCompletenessMetric(threshold=0.5, model=judge, include_reason=True)
    failures = []
    for convo in CONVERSATIONS:
        history: list[dict] = []
        turns: list[LLMTestCase] = []
        for user_msg, _ in convo:
            reply = chatbot.chat(user_msg, history=history).reply
            history.append({"role": "user", "content": user_msg})
            history.append({"role": "assistant", "content": reply})
            turns.append(LLMTestCase(input=user_msg, actual_output=reply))
        ctc = ConversationalTestCase(turns=turns)
        metric.measure(ctc)
        if not metric.is_successful():
            failures.append((convo[0][0], metric.score, metric.reason))
    assert not failures, f"Conversational-relevancy failures: {failures}"
