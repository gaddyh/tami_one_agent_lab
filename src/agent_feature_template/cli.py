"""Interactive CLI for the reminder agent.

Usage:
    python -m src.agent_feature_template.cli
"""
from __future__ import annotations

from datetime import datetime, timezone

from .agent import run_agent
from .render import render_output
from .schemas import ConversationTurn, ReminderInput


def main() -> None:
    print("Reminder Agent (type 'quit' to exit)")
    print()

    prior_context: list[ConversationTurn] | None = None

    while True:
        try:
            text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if text.lower() in ("quit", "exit", "q"):
            break
        if not text:
            continue

        now = datetime.now(timezone.utc)
        input_data = ReminderInput(
            input_id=f"cli-{now.timestamp()}",
            text=text,
            current_time=now,
            prior_context=prior_context,
        )

        output = run_agent(input_data)
        rendered = render_output(output)
        print(f"agent> {rendered}")
        print()

        # Track conversation context
        if prior_context is None:
            prior_context = []
        prior_context.append(ConversationTurn(role="user", text=text))
        prior_context.append(ConversationTurn(role="agent", text=rendered))

        # Reset context after a reminder is created or input is ignored
        if output.status in ("created", "ignored"):
            prior_context = None


if __name__ == "__main__":
    main()
