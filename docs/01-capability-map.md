# Capability Map

Start from the desired output and ask:

> What must the system know, decide, or do in order to produce this output?

Do not start from code or infrastructure. Start from capabilities.

## Core product question

```text
Given a user message like "remind me tomorrow to call dad", what task is being requested, when should it happen, is any information missing, and should the agent create a reminder or ask for clarification?
```

## Questions the system must answer

### Input-level questions

- Is this a reminder request? (contains "remind me" or similar intent)
- Is this a continuation of a previous turn? (user answering a clarification question)
- Is the input complete enough to create a reminder, or is something missing?

### Extraction questions

- What is the task/action to be reminded about? ("call dad")
- What date is specified? ("tomorrow", "today", "Monday")
- What time is specified? ("3pm", "15:00", "3:30 pm")
- Is there prior context from an earlier turn that this message completes?

### Decision questions

- Are both date and time present?
- If not, which is missing?
- Should the agent ask for the missing field, or create the reminder?
- What clarification question should it ask?

### Output questions

- Should the agent return a Reminder object, or a clarification question?
- What structured fields are required in the Reminder?
- What should the user-facing message say?

---

# Capability Groups

## 1. Input / Data Capabilities

These capabilities are about loading and representing reality.

Potential capabilities:

- Represent a user message (text + optional conversation context)
- Represent prior turns for multi-turn clarification
- Provide current_time for resolving relative dates
- Represent a Reminder object (what, when, reminder_id, created_at)

First-demo version:

```text
Accept text input + optional prior_context + current_time as function arguments.
```

Later production version:

```text
Read from chat APIs, voice transcripts, or messaging webhooks.
```

---

## 2. Intent Classification Capabilities

These capabilities decide whether and how an input should enter the agent pipeline.

Potential capabilities:

- Detect whether the message is a reminder request ("remind me", "remind me to")
- Detect whether the message is a clarification answer (just a time or date, with prior context)
- Detect whether the message is irrelevant (not a reminder request at all)

Example output:

```json
{
  "input_id": "msg-001",
  "intent": "reminder_request",
  "should_process": true,
  "confidence": 0.95
}
```

---

## 3. Extraction Capabilities

These capabilities interpret the relevant input.

Potential capabilities:

- Extract the task description from the reminder request
- Extract the date expression (today, tomorrow, a weekday name)
- Extract the time expression (3pm, 15:00, 3:30 pm, 9 am)
- Merge extracted fields with prior context from earlier turns

Example output:

```json
{
  "task": "call dad",
  "date_raw": "tomorrow",
  "time_raw": null,
  "resolved_date": "2026-07-11",
  "resolved_time": null,
  "evidence": ["remind me tomorrow to call dad"]
}
```

---

## 4. Decision / Clarification Capabilities

These capabilities decide what the agent should do.

Potential capabilities:

- Determine which required fields are missing (date? time? task?)
- Generate an appropriate clarification question for the missing field
- Decide: create reminder vs. ask for clarification
- Assign confidence based on extraction completeness

Example output (clarification needed):

```json
{
  "status": "needs_clarification",
  "missing_fields": ["time"],
  "clarification_question": "What time should I remind you to call dad?",
  "confidence": 0.7
}
```

Example output (reminder created):

```json
{
  "status": "created",
  "reminder": {
    "reminder_id": "r-001",
    "what": "call dad",
    "when": "2026-07-11T15:00:00+03:00"
  },
  "confidence": 0.9
}
```

---

## 5. Output / Rendering Capabilities

These capabilities create the final user-facing or system-facing result.

Potential capabilities:

- Return a structured Reminder object when all fields are present
- Return a clarification question when fields are missing
- Render a human-readable confirmation message

Example output (created):

```text
Reminder created: call dad tomorrow at 3:00 PM
```

Example output (clarification):

```text
What time should I remind you to call dad?
```

---

# First Demo Feature Order

## Feature 1: Input & Output Schema

Define the ReminderInput, ReminderOutput, and Reminder models.

## Feature 2: Sample Dataset

Create realistic examples covering complete requests, missing-time cases, missing-date cases, and irrelevant inputs.

## Feature 3: Intent Classification

Detect whether a message is a reminder request, a clarification answer, or irrelevant.

## Feature 4: Extraction

Extract task, date, and time from natural language. Merge with prior context.

## Feature 5: Date/Time Resolution

Resolve relative dates (today, tomorrow, weekdays) and parse time expressions into concrete datetimes.

## Feature 6: Clarification Logic

Detect missing fields and generate appropriate clarification questions.

## Feature 7: Reminder Creation

Assemble the final Reminder object when all fields are present.

## Feature 8: Rendering

Produce human-readable confirmation or clarification messages.

## Feature 9: Evaluation Loop

Add examples, metrics, failure inspection, and regression checks.

---

# Later Production Feature Order

Only after the first demo works:

## Feature 10: Real Input Integration

Connect to chat APIs, voice transcripts, or messaging webhooks.

## Feature 11: Persistent State

Store reminders, conversation history, and feedback.

## Feature 12: Scheduling / Triggering

Run a scheduler that fires reminders at the specified time.

## Feature 13: Notifications / Actions

Send push notifications, SMS, emails, or trigger external workflows.

## Feature 14: Feedback Loop

Allow users to mark reminders as helpful, dismiss, snooze, or edit.

## Feature 15: Monitoring and Regression Evaluation

Track quality over time and prevent silent degradation.

---

# Minimal First Demo Pipeline

```text
user message + optional prior context + current_time
→ classify intent (reminder request? clarification answer? irrelevant?)
→ extract task, date, time (merge with prior context if present)
→ decide: all fields present? → create reminder; else → ask clarification
→ return structured output (Reminder or clarification question)
→ evaluate against examples
```

---

# Core Principle

The agent should not guess when information is missing.

The first intelligence layer is extraction + completeness checking:

```text
Does this message contain enough to create a valid reminder?
```

Only when all required fields are present should the agent create a reminder. Otherwise, it asks a targeted clarification question.
