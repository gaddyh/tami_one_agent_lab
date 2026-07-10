from __future__ import annotations

from .schemas import ReminderOutput, ReminderStatus


def render_output(output: ReminderOutput) -> str:
    """Render a reminder agent output as a human-readable message."""

    if output.rendered_message:
        return output.rendered_message

    if output.status == ReminderStatus.CREATED and output.reminder:
        when_str = output.reminder.when.strftime("%B %d at %I:%M %p").lstrip("0")
        return f"Reminder created: {output.reminder.what} on {when_str}"

    if output.status == ReminderStatus.NEEDS_CLARIFICATION and output.clarification_question:
        return output.clarification_question

    if output.status == ReminderStatus.IGNORED:
        return "I didn't catch a reminder request. Could you rephrase?"

    return f"Status: {output.status}"
