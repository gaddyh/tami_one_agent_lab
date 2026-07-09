from __future__ import annotations

from src.agent_feature_template.schemas import AgentOutput


def keyword_hit(text: str | None, expected_keywords: list[str]) -> bool:
    if not expected_keywords:
        return True
    if not text:
        return False
    normalized = text.lower()
    return all(keyword.lower() in normalized for keyword in expected_keywords)


def score_output(predicted: AgentOutput, expected: dict) -> dict:
    classification_ok = predicted.classification == expected.get("classification")
    should_process_ok = predicted.should_process == expected.get("should_process")
    decision_ok = predicted.decision == expected.get("decision")
    priority_ok = predicted.priority == expected.get("priority")
    summary_ok = keyword_hit(
        predicted.summary,
        expected.get("expected_summary_keywords", []),
    )
    recommendation_ok = keyword_hit(
        predicted.recommended_next_step,
        expected.get("expected_recommendation_keywords", []),
    )

    passed = all([
        classification_ok,
        should_process_ok,
        decision_ok,
        priority_ok,
        summary_ok,
        recommendation_ok,
    ])

    return {
        "passed": passed,
        "classification_ok": classification_ok,
        "should_process_ok": should_process_ok,
        "decision_ok": decision_ok,
        "priority_ok": priority_ok,
        "summary_ok": summary_ok,
        "recommendation_ok": recommendation_ok,
    }
