from __future__ import annotations

from datetime import datetime

from src.agent_feature_template.render import render_output
from src.agent_feature_template.schemas import Reminder, ReminderOutput, ReminderStatus


def test_render_created_reminder():
    output = ReminderOutput(
        input_id="msg-001",
        status=ReminderStatus.CREATED,
        reminder=Reminder(
            reminder_id="r-001",
            what="call dad",
            when=datetime(2026, 7, 11, 15, 0, 0),
            created_at=datetime(2026, 7, 10, 0, 51, 0),
        ),
        confidence=0.9,
    )
    rendered = render_output(output)
    assert "call dad" in rendered
    assert "Reminder created" in rendered


def test_render_needs_clarification():
    output = ReminderOutput(
        input_id="msg-002",
        status=ReminderStatus.NEEDS_CLARIFICATION,
        clarification_question="What time should I remind you to call dad?",
        missing_fields=["time"],
        confidence=0.7,
    )
    rendered = render_output(output)
    assert "What time" in rendered
    assert "call dad" in rendered


def test_render_created_with_rendered_message():
    output = ReminderOutput(
        input_id="msg-001",
        status=ReminderStatus.CREATED,
        reminder=Reminder(
            reminder_id="r-001",
            what="call dad",
            when=datetime(2026, 7, 11, 15, 0, 0),
            created_at=datetime(2026, 7, 10, 0, 51, 0),
        ),
        confidence=0.9,
        language="he",
        rendered_message="תזכורת נוצרה: להתקשר לאבא ב-11 ביולי בשעה 15:00",
    )
    rendered = render_output(output)
    assert "תזכורת" in rendered


def test_render_ignored():
    output = ReminderOutput(
        input_id="msg-003",
        status=ReminderStatus.IGNORED,
        confidence=0.9,
    )
    rendered = render_output(output)
    assert "didn't catch" in rendered
