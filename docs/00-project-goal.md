# Project Goal

This file defines the product goal before implementation begins.

## Desired final output

A conversational reminder agent that parses natural language requests, asks for missing information (like time), and produces a structured reminder object.

Example interaction:

```text
User: "Remind me tomorrow to call dad"
Agent: "What time should I remind you to call dad?"
User: "3pm"
Agent: "Reminder created: call dad tomorrow at 3:00 PM"
```

Final structured output:

```json
{
  "input_id": "msg-001",
  "status": "created",
  "reminder": {
    "reminder_id": "r-001",
    "what": "call dad",
    "when": "2026-07-11T15:00:00+03:00",
    "created_at": "2026-07-10T00:51:00+03:00"
  },
  "clarification_question": null,
  "missing_fields": [],
  "confidence": 0.9
}
```

## Product promise

In one sentence, what useful job should the agent do?

```text
Given a natural language reminder request, the agent should extract the task and timing, ask for any missing details, and produce a structured reminder object.
```

## User / operator

Who is this for?

```text
Anyone who wants to set reminders conversationally — personal users, busy professionals, or as a building block for a larger assistant.
```

## First demo scope

The first demo should prove the core intelligence loop without production infrastructure.

In scope:

- Parse natural language reminder requests ("remind me tomorrow to call dad")
- Extract task description, date, and time from text
- Ask clarifying questions when time or date is missing
- Handle multi-turn conversation (user answers clarification, agent creates reminder)
- Produce a structured Reminder object with resolved datetime
- Support relative dates (today, tomorrow) and common time formats (3pm, 15:00, 3:30 pm)

Out of scope for first demo:

- production database
- background scheduler
- provider integration
- auth / tenancy
- deployment
- notification sending
- recurring reminders
- natural language date parsing beyond today/tomorrow/weekdays

## First proof question

What is the smallest question this project must answer?

```text
Given "remind me tomorrow to call dad", can the agent detect that time is missing, ask for it, and then create a valid reminder object once the user provides the time?
```

## Success criteria

- Agent correctly extracts the task from a reminder request
- Agent detects when time is missing and asks a clear clarification question
- Agent combines a clarification answer with prior context to create a complete reminder
- Agent resolves relative dates (tomorrow → concrete date) using a provided current_time
- Reminder object contains a valid ISO datetime
- All tests pass
