"""Verify stratification of eval datasets.

Usage:
    python scripts/verify_stratification.py
    python scripts/verify_stratification.py --data-dir data/examples
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


EXPECTED = {
    "train": {
        "total": 100,
        "strata": {
            "created": 25,
            "missing_time": 15,
            "missing_date": 15,
            "missing_both": 15,
            "ignored": 15,
            "multi_turn": 10,
            "edge": 5,
        },
    },
    "val": {
        "total": 30,
        "strata": {
            "created": 8,
            "missing_time": 4,
            "missing_date": 4,
            "missing_both": 4,
            "ignored": 4,
            "multi_turn": 3,
            "edge": 3,
        },
    },
    "test": {
        "total": 30,
        "strata": {
            "created": 8,
            "missing_time": 4,
            "missing_date": 4,
            "missing_both": 4,
            "ignored": 4,
            "multi_turn": 3,
            "edge": 3,
        },
    },
}

# Map id prefixes to stratum names
PREFIX_TO_STRATUM = {
    "created": "created",
    "miss_time": "missing_time",
    "miss_date": "missing_date",
    "miss_both": "missing_both",
    "ignored": "ignored",
    "multi_time": "multi_turn",
    "multi_date": "multi_turn",
    "edge_no_task": "edge",
}


def classify_stratum(case: dict) -> str:
    """Classify a case into a stratum by its expected status, missing fields, and prior context."""
    expected = case.get("expected", {})
    status = expected.get("status", "")
    missing = set(expected.get("missing_fields", []))
    has_prior = case.get("input", {}).get("prior_context") is not None

    if status == "ignored":
        return "ignored"
    if status == "created":
        if has_prior:
            return "multi_turn"
        return "created"
    if status == "needs_clarification":
        if has_prior:
            return "multi_turn"
        if missing == {"time"}:
            return "missing_time"
        if missing == {"date"}:
            return "missing_date"
        if missing == {"date", "time"}:
            return "missing_both"
        if "task" in missing:
            return "edge"
    return "unknown"


def load_jsonl(path: Path) -> list[dict]:
    cases = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def verify_split(name: str, path: Path, expected: dict) -> bool:
    cases = load_jsonl(path)
    actual_total = len(cases)

    actual_strata = Counter()
    for case in cases:
        stratum = classify_stratum(case)
        actual_strata[stratum] += 1

    ok = True

    print(f"\n{'=' * 50}")
    print(f"Split: {name} ({path})")
    print(f"{'=' * 50}")
    print(f"  Total: {actual_total} (expected {expected['total']})")
    if actual_total != expected["total"]:
        ok = False
        print(f"  [FAIL] Total mismatch")

    print(f"\n  {'Stratum':<20} {'Actual':>8} {'Expected':>10} {'OK':>6}")
    print(f"  {'-' * 44}")

    all_strata = sorted(set(list(actual_strata.keys()) + list(expected["strata"].keys())))
    for stratum in all_strata:
        actual = actual_strata.get(stratum, 0)
        exp = expected["strata"].get(stratum, 0)
        match = "OK" if actual == exp else "FAIL"
        if actual != exp:
            ok = False
        print(f"  {stratum:<20} {actual:>8} {exp:>10} {match:>6}")

    # Also check by id prefix for cross-validation
    prefix_counts = Counter()
    for case in cases:
        prefix = case["id"].rsplit("_", 1)[0]
        stratum = PREFIX_TO_STRATUM.get(prefix, "unknown")
        prefix_counts[stratum] += 1

    print(f"\n  By id prefix:")
    print(f"  {'Stratum':<20} {'Count':>8}")
    print(f"  {'-' * 30}")
    for stratum in sorted(prefix_counts):
        print(f"  {stratum:<20} {prefix_counts[stratum]:>8}")

    return ok


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data/examples"))
    args = parser.parse_args()

    all_ok = True
    for split_name, expected in EXPECTED.items():
        path = args.data_dir / f"{split_name}.jsonl"
        if not path.exists():
            print(f"[SKIP] {path} does not exist")
            continue
        ok = verify_split(split_name, path, expected)
        all_ok = all_ok and ok

    print(f"\n{'=' * 50}")
    if all_ok:
        print("All stratification checks PASSED")
    else:
        print("Some stratification checks FAILED")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
