# Design: <feature-name>

## Current code touched

- `src/...`
- `eval/...`
- `tests/...`
- `data/examples/...`

## Data model

Describe Pydantic models, tables, or structured objects.

```python
class InputModel(BaseModel):
    ...

class OutputModel(BaseModel):
    ...
```

## API / function boundary

Define the smallest stable boundary.

```python
def run_feature(input: InputModel) -> OutputModel:
    ...
```

## Flow

1. Receive input.
2. Validate input.
3. Classify or transform.
4. Decide or render.
5. Return typed output.

## Agent behavior

If this feature uses an LLM, define:

- prompt responsibility,
- structured output schema,
- allowed assumptions,
- forbidden behavior,
- confidence policy,
- fallback behavior.

## Tool behavior

If this feature uses tools, define:

- available tools,
- required arguments,
- forbidden tool calls,
- validation rules,
- behavior when arguments are missing.

## Decisions

- We chose X because Y.
- We are not doing Z yet because it is not needed for the first demo.

## Risks

| Risk | Mitigation |
|---|---|
| <risk> | <mitigation> |

## Eval plan

Which examples prove this feature works?

- positive examples:
- negative examples:
- edge cases:
