# Design: reminder-agent

## Current code touched

- `src/agent_feature_template/schemas.py`
- `src/agent_feature_template/agent.py`
- `src/agent_feature_template/render.py`
- `src/agent_feature_template/signatures.py` (new)
- `eval/run_eval.py`
- `eval/metrics.py`
- `tests/test_agent.py`
- `data/examples/example_cases.jsonl`
- `pyproject.toml`

## Data model

```python
class ConversationTurn(BaseModel):
    role: str  # "user" or "agent"
    text: str

class Reminder(BaseModel):
    reminder_id: str
    what: str
    when: datetime
    created_at: datetime

class ReminderInput(BaseModel):
    input_id: str
    text: str
    current_time: datetime
    prior_context: list[ConversationTurn] | None = None

class ReminderOutput(BaseModel):
    input_id: str
    status: str  # "created", "needs_clarification", "ignored"
    reminder: Reminder | None = None
    clarification_question: str | None = None
    missing_fields: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
```

## DSPy signatures

```python
class ClassifyIntent(dspy.Signature):
    """Classify the intent of a user message in the context of a reminder conversation."""
    text: str = dspy.InputField()
    prior_context: str = dspy.InputField(desc="Prior conversation turns, or empty")
    intent: str = dspy.OutputField(desc="reminder_request, clarification_answer, or irrelevant")
    confidence: float = dspy.OutputField()

class ExtractReminder(dspy.Signature):
    """Extract task, date, and time from a reminder request or clarification answer."""
    text: str = dspy.InputField()
    prior_context: str = dspy.InputField(desc="Prior conversation turns, or empty")
    current_time: str = dspy.InputField(desc="ISO datetime for resolving relative dates")
    task: str = dspy.OutputField(desc="The action to be reminded about, or empty if not a reminder")
    date_raw: str = dspy.OutputField(desc="Date expression as written, or empty if not specified")
    time_raw: str = dspy.OutputField(desc="Time expression as written, or empty if not specified")
    resolved_datetime: str = dspy.OutputField(desc="ISO datetime if both date and time are known, or empty")

class GenerateClarification(dspy.Signature):
    """Generate a clarification question for missing reminder fields."""
    task: str = dspy.InputField()
    missing_fields: str = dspy.InputField(desc="Comma-separated: time, date, or both")
    question: str = dspy.OutputField(desc="Natural language clarification question referencing the task")
```

## API / function boundary

```python
def run_agent(input: ReminderInput) -> ReminderOutput:
    ...
```

## Flow

1. Receive `ReminderInput` (text, current_time, prior_context).
2. Classify intent via `dspy.Predict(ClassifyIntent)`.
3. If intent is `irrelevant` → return `ReminderOutput(status="ignored")`.
4. If intent is `reminder_request` or `clarification_answer`:
   a. Extract fields via `dspy.ChainOfThought(ExtractReminder)`.
   b. If `clarification_answer`, merge extracted fields with prior context (re-extract from prior user turns + current message).
5. Check completeness: are `task`, `resolved_datetime` all present and valid?
6. If missing fields → generate clarification via `dspy.Predict(GenerateClarification)`, return `needs_clarification`.
7. If complete → assemble `Reminder` object, return `created`.
8. Validate all outputs through Pydantic before returning.

## Agent behavior

- DSPy signatures define structured I/O — no hand-written prompts.
- `dspy.Predict` for classification (simple classification).
- `dspy.ChainOfThought` for extraction (multi-field reasoning).
- `dspy.Predict` for clarification question generation.
- `current_time` passed to extraction signature so LLM can resolve relative dates.
- Pydantic models wrap DSPy outputs for validation and typed boundaries.
- Python orchestrator handles flow control and completeness checking (not the LLM).
- LLM is never asked to decide whether to create vs clarify — Python checks field completeness.
- Fallback: if DSPy output fails Pydantic validation, return `needs_clarification` with low confidence.

## Tool behavior

No tools in first demo. The LLM does extraction and clarification; Python does orchestration and validation.

## Decisions

- We chose DSPy signatures over raw prompts for structured, optimizable I/O.
- We chose `dspy.ChainOfThought` for extraction because multiple fields need reasoning.
- We chose OpenAI GPT-4o as the LLM provider (requires `OPENAI_API_KEY`).
- We pass `current_time` explicitly for testability and deterministic date resolution.
- We keep completeness checking in Python (not LLM) to avoid hallucinated "complete" decisions.
- We are not doing teleprompter optimization yet — first demo uses default DSPy modules.

## Risks

| Risk | Mitigation |
|---|---|
| LLM hallucinates fields not in input | Pydantic validation + completeness check in Python |
| DSPy output format doesn't parse | Use typed signatures with field descriptions; fallback to needs_clarification |
| LLM resolves date incorrectly | Pass current_time explicitly; validate resolved_datetime is a valid ISO datetime |
| Multi-turn context too long | Keep prior_context as raw turns; let LLM extract naturally |
| API key not set in tests | Mock DSPy calls in unit tests; use real LLM only in eval |

## Eval plan

- positive examples: complete request, multi-turn clarification, ambiguous intent ("don't forget")
- negative examples: irrelevant input
- edge cases: missing time only, missing date only, missing both
