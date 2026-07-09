# Agent Feature Template

A reusable, Markdown-first template for designing, building, and evaluating AI agent features in small, testable steps.

Use this repo as a GitHub **template repository**. For every new agent you build, create a new repo from this template, fill the docs, create feature folders, add examples, implement one small task at a time, and evaluate before adding production infrastructure.

## Why this exists

LLMs make it easy to generate too much code too quickly. This template is designed to slow the process down in a useful way:

```text
project goal
→ capability map
→ agent contract
→ feature brief/design/tasks
→ examples
→ implementation
→ tests/eval
→ production infra later
```

The template is intentionally infrastructure-light. Your real project can add FastAPI, databases, queues, schedulers, webhooks, auth, deployment, and provider integrations. This repo focuses on the repeatable agent-development loop.

## Repository structure

```text
.
├── docs/
│   ├── 00-project-goal.md
│   ├── 01-capability-map.md
│   ├── 02-agent-contract.md
│   ├── 03-evaluation.md
│   └── 04-operating-procedure.md
├── features/
│   └── 000-template/
│       ├── 01-brief.md
│       ├── 02-design.md
│       └── 03-tasks.md
├── data/
│   └── examples/
│       └── example_cases.jsonl
├── src/
│   └── agent_feature_template/
│       ├── __init__.py
│       ├── schemas.py
│       ├── agent.py
│       └── render.py
├── eval/
│   ├── __init__.py
│   ├── metrics.py
│   └── run_eval.py
├── tests/
│   ├── test_agent.py
│   ├── test_metrics.py
│   └── test_render.py
├── scripts/
│   └── new_feature.py
├── pyproject.toml
├── Makefile
└── .github/workflows/ci.yml
```

## How to use this template

### 1. Create a new repo from the template

On GitHub:

```text
Use this template → Create a new repository
```

Then clone the new repo:

```bash
git clone https://github.com/<you>/<new-agent-repo>.git
cd <new-agent-repo>
```

### 2. Install locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

### 3. Fill the project docs

Start here:

```text
docs/00-project-goal.md
docs/01-capability-map.md
docs/02-agent-contract.md
docs/03-evaluation.md
docs/04-operating-procedure.md
```

Do not start with code. First define what the agent must do, what capabilities it needs, what input/output contract it follows, and how you will evaluate it.

### 4. Create your first feature

```bash
python scripts/new_feature.py classify-input
```

This creates:

```text
features/001-classify-input/
  01-brief.md
  02-design.md
  03-tasks.md
```

Fill those files, then implement one checklist item at a time.

### 5. Add examples

Add JSONL rows under:

```text
data/examples/
```

The default eval runner uses:

```text
data/examples/example_cases.jsonl
```

Replace it with examples from your actual agent domain.

### 6. Run tests and eval

```bash
make test
make eval
```

## What counts as done

A feature is done only when:

- the Markdown docs match the implementation,
- the schema is clear,
- tests pass,
- eval examples pass or failures are understood,
- and you can explain the feature in one paragraph.

## Core rule

> Do not let the codebase get more than one concept ahead of your understanding.
