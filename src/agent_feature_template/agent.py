from __future__ import annotations

from .schemas import AgentInput, AgentOutput, Classification, Decision, Priority


IRRELEVANT_MARKERS = {
    "unsubscribe",
    "promotion",
    "spam",
    "newsletter",
}

URGENT_MARKERS = {
    "urgent",
    "asap",
    "blocked",
    "deadline",
}

QUESTION_MARKERS = {
    "?",
    "can you",
    "please",
    "update",
    "status",
}


def run_agent(input_data: AgentInput) -> AgentOutput:
    """Small deterministic placeholder agent.

    Replace this function with your real agent implementation while keeping
    a typed input/output boundary and tests/evals around it.
    """

    text_lower = input_data.text.lower()

    if any(marker in text_lower for marker in IRRELEVANT_MARKERS):
        return AgentOutput(
            input_id=input_data.input_id,
            classification=Classification.IRRELEVANT,
            should_process=False,
            summary="Input appears irrelevant to the agent task.",
            decision=Decision.IGNORE,
            priority=Priority.NONE,
            recommended_next_step=None,
            confidence=0.8,
            evidence=[input_data.text],
        )

    priority = Priority.URGENT if any(marker in text_lower for marker in URGENT_MARKERS) else Priority.NORMAL

    if any(marker in text_lower for marker in QUESTION_MARKERS):
        return AgentOutput(
            input_id=input_data.input_id,
            classification=Classification.RELEVANT,
            should_process=True,
            summary="Input appears to request a response or status update.",
            decision=Decision.RESPOND,
            priority=priority,
            recommended_next_step="Send a concise response addressing the request.",
            confidence=0.75,
            evidence=[input_data.text],
        )

    return AgentOutput(
        input_id=input_data.input_id,
        classification=Classification.UNCLEAR,
        should_process=True,
        summary="Input may be relevant, but the required action is unclear.",
        decision=Decision.CLARIFY,
        priority=Priority.LOW,
        recommended_next_step="Ask for clarification before acting.",
        confidence=0.45,
        evidence=[input_data.text],
    )
