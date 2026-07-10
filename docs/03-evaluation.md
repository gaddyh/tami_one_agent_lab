# Evaluation

The evaluation answers:

> Did the agent produce the right structured behavior from the input?

Do not rely only on subjective inspection. Build small examples and evaluate repeatedly.

## Eval loop

```text
write examples
-> run agent
-> compare output to expected behavior
-> inspect failures
-> localize cause
-> change one thing
-> rerun
```

## Dataset plan

**160 total examples**, stratified across decision spaces:

| Split | Count | Purpose |
|-------|-------|---------|
| Train | 100 | Used for DSPy teleprompter optimization (later) |
| Val | 30 | Used for tuning and manual inspection |
| Test | 30 | Held out, only run for final eval |

## Stratification

Proportional split across decision spaces:

| Decision space | Train | Val | Test | Total |
|---|---|---|---|---|
| Created (all fields present) | 25 | 8 | 8 | 41 |
| Missing time only | 15 | 4 | 4 | 23 |
| Missing date only | 15 | 4 | 4 | 23 |
| Missing both date + time | 15 | 4 | 4 | 23 |
| Ignored (irrelevant) | 15 | 4 | 4 | 23 |
| Multi-turn clarification | 10 | 3 | 3 | 16 |
| Edge cases (missing task, etc.) | 5 | 3 | 3 | 11 |

## File layout

```text
data/examples/
  train.jsonl    (100 examples)
  val.jsonl      (30 examples)
  test.jsonl     (30 examples)
```

## Variation dimensions

Each example varies across:

- **Intent phrasing**: "remind me to", "don't forget to", "remind me that I need to", "make sure I"
- **Task variety**: call someone, buy something, submit something, pick up, send, take medication, etc.
- **Date expressions**: today, tomorrow, monday, tuesday, next week, specific dates
- **Time formats**: 3pm, 3 pm, 15:00, 9am, 9:00 am, 3:30 pm, noon, midnight
- **Irrelevant variety**: weather, jokes, questions, greetings, opinions
- **Multi-turn**: user provides time, user provides date, user provides both in one answer

## Metrics

Computed per-split (train / val / test):

### 1. Act vs Verify (precision/recall)

- **Act** = agent creates a reminder (status: created)
- **Verify** = agent asks for clarification (status: needs_clarification)

```text
Act precision    = correctly created / all created
Act recall       = correctly created / all that should be created
Verify precision = correctly clarified / all clarified
Verify recall    = correctly clarified / all that should be clarified
```

### 2. Intent detection (precision/recall)

- **Positive** = message is a reminder request (should process)
- **Negative** = message is irrelevant (should ignore)

```text
Intent precision = correctly identified as reminder / all identified as reminder
Intent recall    = correctly identified as reminder / all actual reminders
```

### 3. Field extraction accuracy

For created reminders, check each extracted field:

```text
Task accuracy  = % of created reminders where "what" matches expected
Date accuracy  = % of created reminders where resolved date matches expected
Time accuracy  = % of created reminders where resolved time matches expected
```

### 4. Missing-field detection accuracy

For clarification cases, check if the agent identified the right missing fields:

```text
Missing-field accuracy = % of clarification cases where missing_fields set matches expected
```

### Keyword matching

Clarification keyword matching accepts synonyms:

- For missing date: "date" OR "day" OR "when" all match
- For missing time: "time" OR "when" all match
- For missing both: "when" OR ("date" AND "time") all match

## Example JSONL row

```json
{
  "id": "complete_request_001",
  "input": {
    "input_id": "msg-001",
    "text": "remind me tomorrow at 3pm to call dad",
    "current_time": "2026-07-10T00:51:00+03:00",
    "prior_context": null
  },
  "expected": {
    "status": "created",
    "missing_fields": [],
    "reminder_what": "call dad",
    "reminder_when": "2026-07-11T15:00:00+03:00",
    "clarification_keywords": []
  }
}
```

Multi-turn example:

```json
{
  "id": "multi_turn_time_001",
  "input": {
    "input_id": "msg-002",
    "text": "3pm",
    "current_time": "2026-07-10T00:51:30+03:00",
    "prior_context": [
      {"role": "user", "text": "remind me tomorrow to call dad"},
      {"role": "agent", "text": "What time should I remind you to call dad?"}
    ]
  },
  "expected": {
    "status": "created",
    "missing_fields": [],
    "reminder_what": "call dad",
    "reminder_when": "2026-07-11T15:00:00+03:00",
    "clarification_keywords": []
  }
}
```

Clarification example:

```json
{
  "id": "missing_time_001",
  "input": {
    "input_id": "msg-003",
    "text": "remind me tomorrow to call dad",
    "current_time": "2026-07-10T00:51:00+03:00",
    "prior_context": null
  },
  "expected": {
    "status": "needs_clarification",
    "missing_fields": ["time"],
    "reminder_what": null,
    "reminder_when": null,
    "clarification_keywords": ["time", "call dad"]
  }
}
```

## Failure inspection

For every failed example, inspect:

- Was the intent classification wrong?
- Was the task extraction wrong?
- Was the date or time parsed incorrectly?
- Was a missing field not detected?
- Was a clarification question unclear or missing the task reference?
- Was the expected label wrong?
- Is this a missing feature rather than a bug?

## First principle

Do not improve prompts blindly.

First localize the failure.
