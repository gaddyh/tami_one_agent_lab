from __future__ import annotations

from .schemas import AgentOutput, Priority


_PRIORITY_ORDER = {
    Priority.URGENT: 0,
    Priority.NORMAL: 1,
    Priority.LOW: 2,
    Priority.NONE: 3,
}


def render_outputs(outputs: list[AgentOutput]) -> str:
    """Render agent outputs as a compact human-readable report."""

    sorted_outputs = sorted(outputs, key=lambda item: _PRIORITY_ORDER[item.priority])
    lines: list[str] = []

    for index, item in enumerate(sorted_outputs, start=1):
        lines.append(f"{index}. [{item.priority}] {item.summary}")
        lines.append(f"   decision: {item.decision}")
        if item.recommended_next_step:
            lines.append(f"   next: {item.recommended_next_step}")

    return "\n".join(lines)
