# Tasks: reminder-agent

## Rule

One task should be small enough to fully review.

## Checklist

- [ ] Finalize brief.
- [ ] Finalize design.
- [ ] Add `dspy-ai` dependency to pyproject.toml.
- [ ] Define schemas in `schemas.py` (ConversationTurn, Reminder, ReminderInput, ReminderOutput).
- [ ] Define DSPy signatures in `signatures.py` (ClassifyIntent, ExtractReminder, GenerateClarification).
- [ ] Implement DSPy module setup (configure dspy.LM with OpenAI).
- [ ] Implement intent classification (dspy.Predict(ClassifyIntent)).
- [ ] Implement field extraction (dspy.ChainOfThought(ExtractReminder)).
- [ ] Implement prior context merging (re-extract from prior user turns + current message).
- [ ] Implement completeness checking in Python (task + resolved_datetime present?).
- [ ] Implement clarification question generation (dspy.Predict(GenerateClarification)).
- [ ] Implement reminder creation (assemble Reminder object with generated ID).
- [ ] Implement orchestrator in `agent.py` (classify -> extract -> check -> create/clarify).
- [ ] Implement render in `render.py` (human-readable confirmation or clarification).
- [ ] Add example cases to `data/examples/example_cases.jsonl`.
- [ ] Write unit tests (mock DSPy calls).
- [ ] Write eval metrics (precision/recall for act vs verify, intent detection, field accuracy).
- [ ] Run tests.
- [ ] Run eval.
- [ ] Inspect output manually.
- [ ] Update docs if implementation changed the design.

## Manual verification

```bash
make test
make eval
```

Expected:

```text
All tests pass.
Eval reports act precision/recall, verify precision/recall, intent precision/recall,
field extraction accuracy, and missing-field detection accuracy.
```
