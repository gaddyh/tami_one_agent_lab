# Evaluation

The evaluation answers:

> Did the agent produce the right structured behavior from the input?

Do not rely only on subjective inspection. Build small examples and evaluate repeatedly.

## Eval loop

```text
write examples
→ run agent
→ compare output to expected behavior
→ inspect failures
→ localize cause
→ change one thing
→ rerun
```

## Eval dimensions

### 1. Structural correctness

- Valid JSON / Pydantic object.
- Required fields present.
- Enums are valid.
- Confidence is within range.

### 2. Classification correctness

- Correctly identifies relevant vs irrelevant input.
- Correctly identifies subtype/category.
- Does not process irrelevant inputs.

### 3. Situation correctness

- Summary matches source input.
- Key facts are preserved.
- No invented facts.
- Evidence supports the conclusion.

### 4. Decision correctness

- Correct action / ignore / clarify / escalate decision.
- Correct priority.
- Correct ownership of next step.
- Reasonable recommended action.

### 5. Product usefulness

- Output is concise.
- Output is actionable.
- Output avoids noise.
- Output is useful to the intended user/operator.

## Minimal deterministic metrics

Start simple:

- classification exact match,
- should_process exact match,
- decision exact match,
- priority exact match,
- expected keyword coverage in summary,
- expected keyword coverage in recommendation.

## Optional LLM judge

Use an LLM judge only after deterministic metrics become too brittle.

Good candidates for LLM judging:

- semantic equivalence of summaries,
- usefulness of recommended action,
- whether evidence supports the decision.

Keep deterministic checks for enums and structural fields.

## Example JSONL row

```json
{
  "id": "status_update_request",
  "input": {
    "input_id": "example-001",
    "text": "Can you update me on this?"
  },
  "expected": {
    "classification": "relevant",
    "should_process": true,
    "decision": "respond",
    "priority": "normal",
    "expected_summary_keywords": ["status", "update"],
    "expected_recommendation_keywords": ["reply"]
  }
}
```

## Failure inspection

For every failed example, inspect:

- Was the input classification wrong?
- Was the situation misunderstood?
- Was the decision wrong?
- Was the output wording correct but metric too strict?
- Was the expected label wrong?
- Is this a missing feature rather than a bug?

## First principle

Do not improve prompts blindly.

First localize the failure.
