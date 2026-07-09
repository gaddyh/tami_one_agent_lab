# Agent Contract

This file defines the input/output boundary of the agent.

The contract should be stable before implementation begins.

## Agent responsibility

The agent is responsible for:

- receiving a normalized input,
- classifying or interpreting it,
- making a decision,
- returning a structured output,
- and preserving enough evidence to evaluate the result.

The agent is not responsible for production infrastructure unless explicitly added later.

## Input schema

Define what the agent receives.

Example:

```json
{
  "input_id": "example-001",
  "source": "sample",
  "text": "Can you update me on this?",
  "metadata": {
    "created_at": "2026-07-10T09:00:00+03:00"
  }
}
```

## Output schema

Define what the agent returns.

Example:

```json
{
  "input_id": "example-001",
  "classification": "relevant",
  "should_process": true,
  "summary": "The user is asking for a status update.",
  "decision": "respond",
  "priority": "normal",
  "recommended_next_step": "Send a short status update.",
  "confidence": 0.86,
  "evidence": ["Can you update me on this?"]
}
```

## Required behavior

- Return valid structured output.
- Do not invent unsupported facts.
- Use `unclear` or low confidence when information is missing.
- Keep decisions grounded in evidence.
- Separate classification from final decision.
- Separate “relevant” from “action required.”

## Forbidden behavior

- Do not process irrelevant inputs as if they are important.
- Do not call tools without required arguments.
- Do not hide uncertainty.
- Do not produce a confident answer when evidence is weak.
- Do not optimize for nice wording over correctness.

## Confidence policy

Use confidence to express how strongly the output is supported by the input.

Suggested interpretation:

```text
0.90–1.00: strongly supported
0.70–0.89: reasonable but may need review
0.50–0.69: weak / ambiguous
0.00–0.49: unclear or likely not enough information
```

## Clarification policy

If the agent lacks necessary information, it should return a clarification decision rather than guessing.

Example:

```json
{
  "decision": "clarify",
  "recommended_next_step": "Ask which customer this refers to.",
  "confidence": 0.52
}
```
