from __future__ import annotations

import argparse
import json
from pathlib import Path

from eval.metrics import score_output
from src.agent_feature_template.agent import run_agent
from src.agent_feature_template.schemas import AgentInput


DEFAULT_EXAMPLES_PATH = Path("data/examples/example_cases.jsonl")


def iter_examples(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--examples", type=Path, default=DEFAULT_EXAMPLES_PATH)
    args = parser.parse_args()

    total = 0
    passed = 0

    for row in iter_examples(args.examples):
        total += 1
        input_data = AgentInput.model_validate(row["input"])
        predicted = run_agent(input_data)
        result = score_output(predicted, row["expected"])
        if result["passed"]:
            passed += 1

        print(json.dumps({
            "id": row["id"],
            "passed": result["passed"],
            "result": result,
            "predicted": predicted.model_dump(mode="json"),
        }, ensure_ascii=False))

    print(f"\nPassed {passed}/{total}")
    if total == 0 or passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
