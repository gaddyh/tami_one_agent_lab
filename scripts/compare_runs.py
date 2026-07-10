"""Compare eval runs from the runs/ directory.

Usage:
    python -m scripts.compare_runs [run_id1] [run_id2] ...
    python -m scripts.compare_runs  # compare all runs
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

RUNS_DIR = Path("runs")


def load_run(run_dir: Path) -> dict:
    json_files = list(run_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON results in {run_dir}")
    with json_files[0].open("r", encoding="utf-8") as f:
        return json.load(f)


def print_comparison(runs: list[tuple[str, dict]]) -> None:
    if not runs:
        print("No runs found.")
        return

    # Header
    run_ids = [rid for rid, _ in runs]
    col_w = max(len(rid) for rid in run_ids) + 2
    metric_w = 24

    print(f"\n{'Metric':<{metric_w}}", end="")
    for rid in run_ids:
        print(f"{rid:>{col_w}}", end="")
    print()
    print("-" * (metric_w + col_w * len(run_ids)))

    # Pass rate
    print(f"{'Passed':<{metric_w}}", end="")
    for _, data in runs:
        val = f"{data['passed']}/{data['total']}"
        print(f"{val:>{col_w}}", end="")
    print()

    print(f"{'Pass rate':<{metric_w}}", end="")
    for _, data in runs:
        rate = data['passed'] / data['total'] * 100 if data['total'] else 0
        print(f"{rate:.1f}%{'' :>{col_w - 5}}", end="")
    print()

    # Metrics
    m = runs[0][1].get("metrics", {})
    if m:
        for category in ("act", "verify", "intent"):
            for metric in ("precision", "recall"):
                label = f"{category}.{metric}"
                print(f"{label:<{metric_w}}", end="")
                for _, data in runs:
                    val = data.get("metrics", {}).get(category, {}).get(metric, "—")
                    if isinstance(val, float):
                        print(f"{val:>{col_w}.3f}", end="")
                    else:
                        print(f"{str(val):>{col_w}}", end="")
                print()

    # Latency
    lat = runs[0][1].get("latency", {})
    if lat:
        print()
        for stat in ("p50", "p95", "mean", "max"):
            label = f"latency.{stat} (ms)"
            print(f"{label:<{metric_w}}", end="")
            for _, data in runs:
                val = data.get("latency", {}).get(stat, "—")
                if isinstance(val, (int, float)):
                    print(f"{val:>{col_w}}", end="")
                else:
                    print(f"{str(val):>{col_w}}", end="")
            print()

    # Per-language breakdown
    by_lang = runs[0][1].get("by_language", {})
    if by_lang:
        print()
        print("Per-Language:")
        all_langs = set()
        for _, data in runs:
            all_langs |= set(data.get("by_language", {}).keys())
        for lang in sorted(all_langs):
            print(f"  {lang}:", end="")
            for _, data in runs:
                d = data.get("by_language", {}).get(lang)
                if d:
                    print(f"  {d['passed']}/{d['total']} ({d['pass_rate']}%)", end="")
                else:
                    print(f"  —", end="")
            print()

    # Failures
    print()
    all_fail_ids: set[str] = set()
    fail_map: dict[str, list[bool]] = {}
    for rid, data in runs:
        fail_ids = {f["id"] for f in data.get("failures", [])}
        all_fail_ids |= fail_ids

    for rid, data in runs:
        fail_ids = {f["id"] for f in data.get("failures", [])}
        for fid in all_fail_ids:
            fail_map.setdefault(fid, []).append(fid in fail_ids)

    if all_fail_ids:
        print(f"\nFailures by case ({len(all_fail_ids)} unique):")
        print(f"{'Case ID':<{metric_w}}", end="")
        for rid in run_ids:
            print(f"{rid:>{col_w}}", end="")
        print()
        print("-" * (metric_w + col_w * len(run_ids)))

        for fid in sorted(all_fail_ids):
            print(f"{fid:<{metric_w}}", end="")
            for i, (rid, _) in enumerate(runs):
                mark = "FAIL" if fail_map[fid][i] else "ok"
                print(f"{mark:>{col_w}}", end="")
            print()
    else:
        print("\nNo failures in any run.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare eval runs")
    parser.add_argument("run_ids", nargs="*", help="Run IDs to compare (default: all)")
    parser.add_argument("--runs-dir", type=Path, default=RUNS_DIR)
    args = parser.parse_args()

    if args.run_ids:
        run_dirs = [args.runs_dir / rid for rid in args.run_ids]
    else:
        run_dirs = sorted(d for d in args.runs_dir.iterdir() if d.is_dir())

    if not run_dirs:
        print(f"No runs found in {args.runs_dir}")
        return

    runs = []
    for d in run_dirs:
        if not d.exists():
            print(f"Run not found: {d}")
            continue
        try:
            data = load_run(d)
            runs.append((d.name, data))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading {d}: {e}")

    if runs:
        print_comparison(runs)


if __name__ == "__main__":
    main()
