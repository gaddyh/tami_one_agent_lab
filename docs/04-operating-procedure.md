# Operating Procedure

This file defines how to work with the repo.

## Big-goal decomposition

For every new agent project:

1. Write the desired final output or behavior.
2. Ask what the system must know to produce it.
3. Turn each knowledge/decision need into a capability.
4. Split capabilities into:
   - input/data,
   - intent classification,
   - extraction,
   - decision/clarification,
   - output/rendering.
5. Pick the smallest demo path.
6. Turn each step into a feature.
7. For each feature, create brief/design/tasks.
8. Implement one task at a time.
9. Evaluate before adding production infrastructure.

## Feature procedure

Each feature has exactly three Markdown files:

```text
features/<feature-name>/
  01-brief.md
  02-design.md
  03-tasks.md
```

### 01-brief.md

Define:

- goal,
- user value,
- requirements,
- non-goals,
- examples,
- edge cases,
- success criteria.

### 02-design.md

Define:

- schemas,
- function boundaries,
- flow,
- agent behavior,
- risks,
- design decisions,
- eval plan.

### 03-tasks.md

Define small implementation steps.

One checkbox should be small enough to fully review.

## Implementation rule

Implement only one task at a time.

After each task:

```text
run tests
→ inspect output
→ update docs if reality changed
→ commit
```

## Evaluation rule

Every agent behavior needs examples.

If a feature changes behavior, add or update JSONL examples before trusting it.

## Slow rule

> Do not let the codebase get more than one concept ahead of your understanding.

## Done rule

A feature is not done when code exists.

A feature is done when:

- docs match reality,
- tests pass,
- eval examples pass or failures are understood,
- and you can explain the feature in one paragraph.

## Commit style

Prefer small commits:

```text
docs: define reminder agent goal and contract
schema: add ReminderInput and ReminderOutput models
eval: add missing-time and missing-date examples
agent: implement intent classification and task extraction
test: cover multi-turn clarification flow
```
