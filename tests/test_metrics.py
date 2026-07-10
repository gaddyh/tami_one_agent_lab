from __future__ import annotations

from src.agent_feature_template.schemas import ReminderOutput, ReminderStatus


def test_reminder_status_values():
    assert ReminderStatus.CREATED == "created"
    assert ReminderStatus.NEEDS_CLARIFICATION == "needs_clarification"
    assert ReminderStatus.IGNORED == "ignored"
