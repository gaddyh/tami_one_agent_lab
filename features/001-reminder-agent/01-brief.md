# Feature: reminder-agent

## Goal

Build a conversational reminder agent that parses natural language requests, asks for missing info, and creates structured reminder objects using DSPy-powered LLM extraction.

## User value

Users can set reminders in natural language without remembering exact syntax. The agent asks targeted questions when information is missing, making the interaction feel conversational rather than form-based.

## Capability group

- input/data
- intent classification
- extraction
- decision/clarification
- output/rendering

## Requirements

- Must detect reminder intent from phrases like "remind me", "don't forget to"
- Must extract task, date, and time from natural language using DSPy
- Must ask a targeted clarification question when a required field is missing
- Must merge prior conversation context when user is answering a clarification
- Must resolve relative dates (today, tomorrow) using `current_time`
- Must use typed DSPy signatures (not free-form prompts)
- Must validate LLM output with Pydantic schemas
- Must not create a reminder with missing fields
- Must not guess time or date that wasn't provided

## Non-goals

- We are not doing scheduling or triggering
- We are not handling notifications or push messages
- We are not doing persistent storage
- We are not handling recurring reminders
- We are not doing teleprompter optimization yet (first demo uses default DSPy modules)

## Input examples

Single-turn:

```json
{
  "input_id": "msg-001",
  "text": "remind me tomorrow to call dad",
  "current_time": "2026-07-10T00:51:00+03:00",
  "prior_context": null
}
```

Multi-turn (second turn):

```json
{
  "input_id": "msg-002",
  "text": "3pm",
  "current_time": "2026-07-10T00:51:30+03:00",
  "prior_context": [
    {"role": "user", "text": "remind me tomorrow to call dad"},
    {"role": "agent", "text": "What time should I remind you to call dad?"}
  ]
}
```

## Expected output examples

Reminder created:

```json
{
  "input_id": "msg-002",
  "status": "created",
  "reminder": {
    "reminder_id": "r-001",
    "what": "call dad",
    "when": "2026-07-11T15:00:00+03:00",
    "created_at": "2026-07-10T00:51:30+03:00"
  },
  "clarification_question": null,
  "missing_fields": [],
  "confidence": 0.9
}
```

Needs clarification:

```json
{
  "input_id": "msg-001",
  "status": "needs_clarification",
  "reminder": null,
  "clarification_question": "What time should I remind you to call dad?",
  "missing_fields": ["time"],
  "confidence": 0.7
}
```

## Edge cases

- Irrelevant input ("what's the weather today")
- Ambiguous intent ("don't forget to call dad tomorrow at 3pm")
- Missing time only
- Missing date only
- Missing both date and time
- Multi-turn clarification (user provides partial info across turns)
- LLM hallucinates a field not present in input

## Success criteria

- Agent correctly extracts the task from a reminder request
- Agent detects when time or date is missing and asks a clear clarification question
- Agent combines a clarification answer with prior context to create a complete reminder
- Agent resolves relative dates (tomorrow -> concrete date) using current_time
- Reminder object contains a valid ISO datetime
- All eval cases pass
- All tests pass
