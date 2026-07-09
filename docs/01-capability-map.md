# Capability Map

Start from the desired output and ask:

> What must the system know, decide, or do in order to produce this output?

Do not start from code or infrastructure. Start from capabilities.

## Core product question

```text
Given <input/context>, which information matters, what should the agent decide, and what output/action should it produce?
```

## Questions the system must answer

### Input-level questions

- What kind of input is this?
- Is the input relevant to the agent's job?
- Is the input complete enough to process?
- Does it belong to a known user, case, task, entity, or workflow?
- Is it new, repeated, stale, irrelevant, or unclear?

### Classification questions

Before deeper reasoning, the system should classify the input.

Examples:

- What type of item is this?
- Is this business-relevant or irrelevant?
- Is this actionable or informational?
- Is this safe to automate or does it require human review?
- Should this enter the agent pipeline at all?

### Situation / state questions

- What is currently happening?
- What is the latest meaningful state?
- Is there an open loop?
- Is anything blocked?
- Who owns the next step?
- How long has this been waiting or active?
- What facts support this interpretation?

### Decision questions

- Should the agent act, answer, ignore, escalate, ask a clarification, or wait?
- What priority should this receive?
- What is the recommended next step?
- What confidence does the agent have?
- What should be excluded to avoid noise?

### Output questions

- What should be returned to the user or system?
- What should be shown in a concise summary?
- What structured fields are required?
- What tone or format is expected?
- What should never be invented?

---

# Capability Groups

## 1. Input / Data Capabilities

These capabilities are about loading and representing reality.

Potential capabilities:

- Load sample inputs.
- Represent raw input records.
- Represent normalized input.
- Represent entities/cases/tasks.
- Represent timestamps and source metadata.
- Keep enough evidence to explain decisions.

First-demo version:

```text
Read static JSONL examples from data/examples.
```

Later production version:

```text
Read from real APIs, webhooks, databases, queues, files, or user messages.
```

---

## 2. Classification Capabilities

These capabilities decide whether and how an input should enter the agent pipeline.

Potential capabilities:

- Classify input type.
- Detect relevance.
- Detect ownership / associated entity.
- Detect whether this is actionable, informational, duplicate, stale, or irrelevant.
- Detect whether the item should be ignored, processed, escalated, or held for clarification.

Example output:

```json
{
  "input_id": "example-001",
  "classification": "relevant",
  "subtype": "task_request",
  "should_process": true,
  "confidence": 0.91
}
```

Important rule:

```text
The agent should not reason deeply about every input. First decide whether the input deserves attention.
```

---

## 3. Situation Understanding Capabilities

These capabilities interpret the relevant input.

Potential capabilities:

- Extract current situation.
- Identify open loop.
- Identify blocker.
- Identify owner of next step.
- Extract key entities.
- Extract deadlines or elapsed time.
- Preserve evidence from the source input.

Example output:

```json
{
  "summary": "The user asked for a status update and has not received a reply.",
  "open_loop": true,
  "next_step_owner": "agent_owner",
  "evidence": ["Can you update me on this?"]
}
```

---

## 4. Decision Capabilities

These capabilities decide what the agent should do.

Potential capabilities:

- Decide action required.
- Decide priority.
- Decide whether to ask a clarification.
- Decide whether to escalate.
- Decide whether to include in a final output.
- Suppress duplicates.
- Decide confidence.

Example output:

```json
{
  "action_required": true,
  "priority": "normal",
  "decision": "respond",
  "recommended_next_step": "Send a short status update.",
  "confidence": 0.84
}
```

---

## 5. Action / Tool Capabilities

Only include this group if the agent will call tools or perform actions.

Potential capabilities:

- Select tool.
- Build tool arguments.
- Validate arguments.
- Detect missing required information.
- Avoid forbidden tool calls.
- Interpret tool results.
- Decide next step after tool result.

Example output:

```json
{
  "tool_name": "create_task",
  "arguments": {
    "title": "Follow up with customer",
    "due_date": "2026-07-11"
  }
}
```

---

## 6. Output / Rendering Capabilities

These capabilities create the final user-facing or system-facing result.

Potential capabilities:

- Render concise text.
- Return structured JSON.
- Group by priority/category.
- Explain reasoning briefly.
- Include evidence when useful.
- Keep tone appropriate.
- Avoid verbosity and noise.

Example output:

```text
You have 2 items that need attention:
1. Customer A is waiting for a reply.
2. Customer B is missing a document.
```

---

# First Demo Feature Order

Use this as a default starting point. Rename features for your domain.

## Feature 1: Input Schema

Define the raw and normalized input objects.

## Feature 2: Sample Dataset

Create realistic examples covering success cases, edge cases, and irrelevant cases.

## Feature 3: Input Classification

Decide whether an input is relevant and should enter the pipeline.

## Feature 4: Output Schema

Define the structured object the agent must produce.

## Feature 5: Situation Extraction

Extract the current situation from relevant inputs.

## Feature 6: Decision Logic

Decide action required, priority, escalation, clarification, or ignore.

## Feature 7: Rendering / Response Generation

Produce the final user-facing or system-facing output.

## Feature 8: Evaluation Loop

Add examples, metrics, failure inspection, and regression checks.

---

# Later Production Feature Order

Only after the first demo works:

## Feature 9: Real Input Integration

Connect to real APIs, webhooks, files, or databases.

## Feature 10: Persistent State

Store inputs, outputs, decisions, and feedback.

## Feature 11: Scheduling / Triggering

Run periodically or in response to events.

## Feature 12: Notifications / Actions

Send messages, call tools, update systems, or trigger workflows.

## Feature 13: Feedback Loop

Allow users to mark outputs as useful, wrong, noisy, low priority, or already handled.

## Feature 14: Monitoring and Regression Evaluation

Track quality over time and prevent silent degradation.

---

# Minimal First Demo Pipeline

```text
sample inputs
→ classify relevance
→ ignore irrelevant inputs
→ extract situation from relevant inputs
→ decide action/priority
→ render final output
→ evaluate against examples
```

---

# Core Principle

The system should not process everything equally.

The first intelligence layer is classification:

```text
Should this input enter the agent pipeline at all?
```

Only after that should the system reason about situation, decision, action, and rendering.
