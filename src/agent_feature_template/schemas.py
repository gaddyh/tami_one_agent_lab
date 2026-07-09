from __future__ import annotations

from enum import StrEnum
from pydantic import BaseModel, Field


class Classification(StrEnum):
    RELEVANT = "relevant"
    IRRELEVANT = "irrelevant"
    UNCLEAR = "unclear"


class Decision(StrEnum):
    RESPOND = "respond"
    IGNORE = "ignore"
    CLARIFY = "clarify"
    ESCALATE = "escalate"


class Priority(StrEnum):
    URGENT = "urgent"
    NORMAL = "normal"
    LOW = "low"
    NONE = "none"


class AgentInput(BaseModel):
    """Normalized input for one agent decision.

    Replace or extend this model in your project.
    """

    input_id: str
    text: str
    source: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    """Structured output for one agent decision.

    Replace or extend this model in your project.
    """

    input_id: str
    classification: Classification
    should_process: bool
    summary: str
    decision: Decision
    priority: Priority
    recommended_next_step: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
