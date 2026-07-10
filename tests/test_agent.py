from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from src.agent_feature_template.agent import run_agent
from src.agent_feature_template.schemas import (
    ConversationTurn,
    ReminderInput,
    ReminderStatus,
)

TZ = timezone(timedelta(hours=3))
CURRENT_TIME = datetime(2026, 7, 10, 0, 51, 0, tzinfo=TZ)
EXPECTED_WHEN = datetime(2026, 7, 11, 15, 0, 0, tzinfo=TZ)


def _make_input(text: str, prior_context=None, input_id="msg-test") -> ReminderInput:
    return ReminderInput(
        input_id=input_id,
        text=text,
        current_time=CURRENT_TIME,
        prior_context=prior_context,
    )


def _mock_module(response: dict):
    mock = MagicMock()
    mock.return_value = MagicMock(**response)
    return mock


def _predict_side_effect(*responses: dict):
    """Return a side_effect that pops responses in order, reusing the last if exhausted."""
    pool = list(responses)
    def _fn(sig):
        if pool:
            return _mock_module(pool.pop(0))
        return _mock_module(responses[-1])
    return _fn


@patch("src.agent_feature_template.agent.dspy.Predict")
@patch("src.agent_feature_template.agent._ensure_lm")
def test_complete_request_creates_reminder(mock_ensure, mock_predict_cls):
    mock_predict_cls.side_effect = _predict_side_effect(
        {"intent": "reminder_request", "language": "en", "confidence": 0.95},
        {"task": "call dad", "date_raw": "tomorrow", "time_raw": "3pm",
         "resolved_datetime": "2026-07-11T15:00:00+03:00"},
        {"question": "unused"},
        {"message": "Reminder created: call dad on July 11 at 03:00 PM"},
    )

    output = run_agent(_make_input("remind me tomorrow at 3pm to call dad"))

    assert output.status == ReminderStatus.CREATED
    assert output.reminder is not None
    assert output.reminder.what == "call dad"
    assert output.reminder.when == EXPECTED_WHEN
    assert output.missing_fields == []
    assert output.clarification_question is None
    assert output.language == "en"
    assert output.rendered_message is not None
    assert "total_ms" in output.timings
    assert "classify_ms" in output.timings
    assert "extract_ms" in output.timings
    assert "render_ms" in output.timings


@patch("src.agent_feature_template.agent.dspy.Predict")
@patch("src.agent_feature_template.agent._ensure_lm")
def test_missing_time_asks_clarification(mock_ensure, mock_predict_cls):
    mock_predict_cls.side_effect = _predict_side_effect(
        {"intent": "reminder_request", "language": "en", "confidence": 0.9},
        {"task": "call dad", "date_raw": "tomorrow", "time_raw": "",
         "resolved_datetime": ""},
        {"question": "What time should I remind you to call dad?"},
        {"message": "unused"},
    )

    output = run_agent(_make_input("remind me tomorrow to call dad"))

    assert output.status == ReminderStatus.NEEDS_CLARIFICATION
    assert "time" in output.missing_fields
    assert output.clarification_question is not None
    assert "call dad" in output.clarification_question.lower()


@patch("src.agent_feature_template.agent.dspy.Predict")
@patch("src.agent_feature_template.agent._ensure_lm")
def test_missing_date_asks_clarification(mock_ensure, mock_predict_cls):
    mock_predict_cls.side_effect = _predict_side_effect(
        {"intent": "reminder_request", "language": "en", "confidence": 0.9},
        {"task": "call mom", "date_raw": "", "time_raw": "3pm",
         "resolved_datetime": ""},
        {"question": "What day should I remind you to call mom?"},
        {"message": "unused"},
    )

    output = run_agent(_make_input("remind me at 3pm to call mom"))

    assert output.status == ReminderStatus.NEEDS_CLARIFICATION
    assert "date" in output.missing_fields
    assert output.clarification_question is not None
    assert "call mom" in output.clarification_question.lower()


@patch("src.agent_feature_template.agent.dspy.Predict")
@patch("src.agent_feature_template.agent._ensure_lm")
def test_missing_both_asks_clarification(mock_ensure, mock_predict_cls):
    mock_predict_cls.side_effect = _predict_side_effect(
        {"intent": "reminder_request", "language": "en", "confidence": 0.8},
        {"task": "buy milk", "date_raw": "", "time_raw": "",
         "resolved_datetime": ""},
        {"question": "When should I remind you to buy milk?"},
        {"message": "unused"},
    )

    output = run_agent(_make_input("remind me to buy milk"))

    assert output.status == ReminderStatus.NEEDS_CLARIFICATION
    assert "date" in output.missing_fields
    assert "time" in output.missing_fields
    assert output.clarification_question is not None
    assert "buy milk" in output.clarification_question.lower()


@patch("src.agent_feature_template.agent.dspy.Predict")
@patch("src.agent_feature_template.agent._ensure_lm")
def test_irrelevant_input_ignored(mock_ensure, mock_predict_cls):
    mock_predict_cls.side_effect = _predict_side_effect(
        {"intent": "irrelevant", "language": "en", "confidence": 0.9},
        {"task": "", "date_raw": "", "time_raw": "", "resolved_datetime": ""},
        {"question": "unused"},
        {"message": "unused"},
    )

    output = run_agent(_make_input("what's the weather today"))

    assert output.status == ReminderStatus.IGNORED
    assert output.reminder is None
    assert output.clarification_question is None


@patch("src.agent_feature_template.agent.dspy.Predict")
@patch("src.agent_feature_template.agent._ensure_lm")
def test_multi_turn_clarification_creates_reminder(mock_ensure, mock_predict_cls):
    mock_predict_cls.side_effect = _predict_side_effect(
        {"intent": "clarification_answer", "language": "en", "confidence": 0.9},
        {"task": "call dad", "date_raw": "tomorrow", "time_raw": "3pm",
         "resolved_datetime": "2026-07-11T15:00:00+03:00"},
        {"question": "unused"},
        {"message": "Reminder created: call dad on July 11 at 03:00 PM"},
    )

    prior = [
        ConversationTurn(role="user", text="remind me tomorrow to call dad"),
        ConversationTurn(role="agent", text="What time should I remind you to call dad?"),
    ]
    output = run_agent(_make_input("3pm", prior_context=prior, input_id="msg-002"))

    assert output.status == ReminderStatus.CREATED
    assert output.reminder is not None
    assert output.reminder.what == "call dad"
    assert output.reminder.when == EXPECTED_WHEN


@patch("src.agent_feature_template.agent.dspy.Predict")
@patch("src.agent_feature_template.agent._ensure_lm")
def test_ambiguous_dont_forget_creates_reminder(mock_ensure, mock_predict_cls):
    mock_predict_cls.side_effect = _predict_side_effect(
        {"intent": "reminder_request", "language": "en", "confidence": 0.85},
        {"task": "call dad", "date_raw": "tomorrow", "time_raw": "3pm",
         "resolved_datetime": "2026-07-11T15:00:00+03:00"},
        {"question": "unused"},
        {"message": "Reminder created: call dad on July 11 at 03:00 PM"},
    )

    output = run_agent(_make_input("don't forget to call dad tomorrow at 3pm"))

    assert output.status == ReminderStatus.CREATED
    assert output.reminder is not None
    assert output.reminder.what == "call dad"


@patch("src.agent_feature_template.agent.dspy.Predict")
@patch("src.agent_feature_template.agent._ensure_lm")
def test_hebrew_input_detects_language(mock_ensure, mock_predict_cls):
    mock_predict_cls.side_effect = _predict_side_effect(
        {"intent": "reminder_request", "language": "he", "confidence": 0.9},
        {"task": "לעשן", "date_raw": "", "time_raw": "",
         "resolved_datetime": ""},
        {"question": "באיזו שעה להזכיר לך לעשן?"},
        {"message": "unused"},
    )

    output = run_agent(_make_input("תזכיר לי עוד שעה לעשן"))

    assert output.status == ReminderStatus.NEEDS_CLARIFICATION
    assert output.language == "he"
    assert output.clarification_question is not None


@patch("src.agent_feature_template.agent.dspy.Predict")
@patch("src.agent_feature_template.agent._ensure_lm")
def test_relative_time_in_hour(mock_ensure, mock_predict_cls):
    mock_predict_cls.side_effect = _predict_side_effect(
        {"intent": "reminder_request", "language": "en", "confidence": 0.9},
        {"task": "call dad", "date_raw": "today", "time_raw": "in an hour",
         "resolved_datetime": "2026-07-10T01:51:00+03:00"},
        {"question": "unused"},
        {"message": "Reminder created: call dad in an hour"},
    )

    output = run_agent(_make_input("remind me in an hour to call dad"))

    assert output.status == ReminderStatus.CREATED
    assert output.reminder is not None
    assert output.reminder.what == "call dad"


@patch("src.agent_feature_template.agent.dspy.Predict")
@patch("src.agent_feature_template.agent._ensure_lm")
def test_hebrew_relative_minute_creates_reminder(mock_ensure, mock_predict_cls):
    mock_predict_cls.side_effect = _predict_side_effect(
        {"intent": "reminder_request", "language": "he", "confidence": 0.9},
        {"task": "לעשן", "date_raw": "today", "time_raw": "עוד דקה",
         "resolved_datetime": "2026-07-10T00:52:00+03:00"},
        {"question": "unused"},
        {"message": "תזכורת נוצרה: לעשן בעוד דקה"},
    )

    output = run_agent(_make_input("תזכיר לי עוד דקה לעשן"))

    assert output.status == ReminderStatus.CREATED
    assert output.reminder is not None
    assert output.reminder.what == "לעשן"
    assert output.language == "he"
    assert output.rendered_message is not None


@patch("src.agent_feature_template.agent.dspy.Predict")
@patch("src.agent_feature_template.agent._ensure_lm")
def test_no_throw_on_llm_exception(mock_ensure, mock_predict_cls):
    """Agent must never raise — it returns a localized fallback on error."""
    mock_predict_cls.side_effect = RuntimeError("LLM exploded")

    output = run_agent(_make_input("remind me to call dad"))

    assert output.status == ReminderStatus.NEEDS_CLARIFICATION
    assert output.language == "en"
    assert output.clarification_question is not None
    assert "total_ms" in output.timings
