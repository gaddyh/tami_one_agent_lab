# Agent Contract

This file defines the input/output boundary of the agent.

The contract should be stable before implementation begins.

## Agent responsibility

The agent is responsible for:

- receiving a user message with optional prior conversation context,
- classifying the intent (reminder request, clarification answer, or irrelevant),
- extracting task, date, and time from the message,
- merging with prior context when the user is answering a clarification,
- deciding whether all required fields are present,
- returning either a Reminder object or a clarification question,
- and preserving evidence to evaluate the result.

The agent is not responsible for scheduling, sending notifications, or persistent storage.

## Input schema

Define what the agent receives.

Single-turn example:

```json
{
  "input_id": "msg-001",
  "text": "remind me tomorrow to call dad",
  "current_time": "2026-07-10T00:51:00+03:00",
  "prior_context": null
}
```

Multi-turn example (second turn):

```json
{
  "input_id": "msg-002",
  "text": "3pm",
  "current_time": "2026-07-10T00:51:30+03:00",
  "prior_context": [
    {
      "role": "user",
      "text": "remind me tomorrow to call dad"
    },
    {
      "role": "agent",
      "text": "What time should I remind you to call dad?"
    }
  ]
}
```

The agent receives raw conversation turns in `prior_context` and is responsible for extracting and merging context itself. No pre-processed fields are passed in.

## Output schema

Define what the agent returns.

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

Irrelevant:

```json
{
  "input_id": "msg-003",
  "status": "ignored",
  "reminder": null,
  "clarification_question": null,
  "missing_fields": [],
  "confidence": 0.9
}
```

## Required behavior

- Return valid structured output for every input.
- Extract task, date, and time from natural language.
- Resolve relative dates using `current_time`.
- Ask for missing fields with a specific, human-readable question.
- Merge `prior_context` with new extraction when user is answering a clarification.
- Generate a unique `reminder_id` for each created reminder.

## Forbidden behavior

- Do not create a reminder with missing required fields.
- Do not guess a time or date that wasn't provided.
- Do not ignore `prior_context` when the user is answering a clarification.
- Do not process irrelevant inputs as reminder requests.

## Confidence policy

Use confidence to express how strongly the output is supported by the input.

```text
0.90-1.00: all fields extracted and resolved
0.70-0.89: task extracted, one field missing (clarification needed)
0.50-0.69: ambiguous input, multiple fields missing
0.00-0.49: input is not a reminder request
```

## Clarification policy

If the agent lacks necessary information, it should return a clarification question rather than guessing.

```text
time missing:  "What time should I remind you to {task}?"
date missing:  "What day should I remind you to {task}?"
both missing:  "When should I remind you to {task}?"
```
