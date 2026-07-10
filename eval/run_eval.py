from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path

from eval.metrics import compute_precision_recall, score_output
from src.agent_feature_template.agent import run_agent
from src.agent_feature_template.render import render_output
from src.agent_feature_template.schemas import ConversationTurn, ReminderInput, ReminderStatus


DEFAULT_DATA_DIR = Path("data/examples")
DEFAULT_CONVERSATIONS_DIR = Path("data/conversations")
RUNS_DIR = Path("runs")


def iter_examples(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def _parse_input(row: dict) -> ReminderInput:
    input_data = dict(row["input"])
    if input_data.get("prior_context"):
        input_data["prior_context"] = [
            ConversationTurn(**turn) for turn in input_data["prior_context"]
        ]
    return ReminderInput.model_validate(input_data)


def _extract_language(row: dict) -> str:
    return row.get("language", row.get("input", {}).get("language", "en"))


def _extract_stratum(row: dict) -> str:
    return row.get("id", "").rsplit("_", 1)[0] if "_" in row.get("id", "") else "unknown"


def _percentiles(values: list[float]) -> dict:
    if not values:
        return {"p50": 0, "p95": 0, "mean": 0, "max": 0}
    s = sorted(values)
    n = len(s)
    return {
        "p50": round(s[n // 2], 2),
        "p95": round(s[min(int(n * 0.95), n - 1)], 2),
        "mean": round(statistics.mean(s), 2),
        "max": round(s[-1], 2),
    }


def run_split(path: Path, verbose: bool = True) -> dict:
    total = 0
    passed = 0
    predictions: list[dict] = []
    failures: list[dict] = []
    per_case: list[dict] = []
    latencies: list[float] = []
    lang_pass: dict[str, list[bool]] = {}
    stratum_pass: dict[str, list[bool]] = {}
    lang_latency: dict[str, list[float]] = {}

    for row in iter_examples(path):
        total += 1
        input_data = _parse_input(row)
        predicted = run_agent(input_data)
        result = score_output(predicted, row["expected"])
        lang = _extract_language(row)
        stratum = _extract_stratum(row)
        total_ms = predicted.timings.get("total_ms", 0)
        latencies.append(total_ms)
        lang_pass.setdefault(lang, []).append(result["passed"])
        stratum_pass.setdefault(stratum, []).append(result["passed"])
        lang_latency.setdefault(lang, []).append(total_ms)

        if result["passed"]:
            passed += 1
        else:
            failures.append({
                "id": row["id"],
                "input_text": row["input"]["text"],
                "result": result,
                "predicted": predicted.model_dump(mode="json"),
                "expected": row["expected"],
            })

        predictions.append({
            "predicted_status": predicted.status.value,
            "expected_status": row["expected"]["status"],
        })

        per_case.append({
            "id": row["id"],
            "passed": result["passed"],
            "result": result,
            "predicted": predicted.model_dump(mode="json"),
            "language": lang,
            "stratum": stratum,
        })

        if verbose:
            print(json.dumps({
                "id": row["id"],
                "passed": result["passed"],
                "result": result,
                "predicted": predicted.model_dump(mode="json"),
            }, ensure_ascii=False))

    metrics = compute_precision_recall(predictions) if predictions else {}

    # Per-language and per-stratum breakdowns
    by_language = {}
    for lang, results in lang_pass.items():
        by_language[lang] = {
            "passed": sum(results),
            "total": len(results),
            "pass_rate": round(sum(results) / len(results) * 100, 1) if results else 0,
            "latency": _percentiles(lang_latency.get(lang, [])),
        }

    by_stratum = {}
    for stratum, results in stratum_pass.items():
        by_stratum[stratum] = {
            "passed": sum(results),
            "total": len(results),
            "pass_rate": round(sum(results) / len(results) * 100, 1) if results else 0,
        }

    return {
        "total": total,
        "passed": passed,
        "metrics": metrics,
        "failures": failures,
        "per_case": per_case,
        "latency": _percentiles(latencies),
        "by_language": by_language,
        "by_stratum": by_stratum,
    }


def run_conversation(path: Path, verbose: bool = True) -> dict:
    """Replay a conversation fixture, threading agent output back as context."""
    with path.open("r", encoding="utf-8") as f:
        conv = json.loads(f.read())

    conv_id = conv.get("id", path.stem)
    lang = conv.get("language", "en")
    current_time = datetime.fromisoformat(conv["current_time"])
    turns = conv.get("turns", [])

    prior_context: list[ConversationTurn] | None = None
    total = len(turns)
    passed = 0
    failures: list[dict] = []
    per_case: list[dict] = []
    latencies: list[float] = []

    for i, turn in enumerate(turns):
        user_text = turn["user"]
        expected = turn["expected"]
        input_data = ReminderInput(
            input_id=f"{conv_id}-t{i}",
            text=user_text,
            current_time=current_time,
            prior_context=prior_context,
        )
        predicted = run_agent(input_data)
        result = score_output(predicted, expected)
        total_ms = predicted.timings.get("total_ms", 0)
        latencies.append(total_ms)

        if result["passed"]:
            passed += 1
        else:
            failures.append({
                "id": f"{conv_id}-t{i}",
                "input_text": user_text,
                "result": result,
                "predicted": predicted.model_dump(mode="json"),
                "expected": expected,
            })

        per_case.append({
            "id": f"{conv_id}-t{i}",
            "passed": result["passed"],
            "result": result,
            "predicted": predicted.model_dump(mode="json"),
            "language": lang,
        })

        if verbose:
            print(json.dumps({
                "id": f"{conv_id}-t{i}",
                "user": user_text,
                "passed": result["passed"],
                "predicted": predicted.model_dump(mode="json"),
            }, ensure_ascii=False))

        # Thread agent output back as context (like cli.py / prod)
        rendered = render_output(predicted)
        if prior_context is None:
            prior_context = []
        prior_context.append(ConversationTurn(role="user", text=user_text))
        prior_context.append(ConversationTurn(role="agent", text=rendered))

        if predicted.status in (ReminderStatus.CREATED, ReminderStatus.IGNORED):
            prior_context = None

    return {
        "total": total,
        "passed": passed,
        "metrics": {},
        "failures": failures,
        "per_case": per_case,
        "latency": _percentiles(latencies),
        "by_language": {lang: {"passed": passed, "total": total,
                                 "pass_rate": round(passed / total * 100, 1) if total else 0,
                                 "latency": _percentiles(latencies)}},
        "by_stratum": {conv_id: {"passed": passed, "total": total,
                                   "pass_rate": round(passed / total * 100, 1) if total else 0}},
    }


def generate_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def write_report(
    run_id: str,
    run_dir: Path,
    split_name: str,
    result: dict,
    notes: str | None = None,
) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)

    # Save raw JSON
    json_path = run_dir / f"{split_name}.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Generate markdown report
    md_path = run_dir / "report.md"
    m = result.get("metrics", {})

    lines = [
        f"# Run {run_id}",
        "",
        f"**Split:** {split_name}",
        f"**Passed:** {result['passed']}/{result['total']}",
        f"**Timestamp:** {datetime.now(timezone.utc).isoformat()}",
        "",
    ]

    if notes:
        lines.append(f"**Notes:** {notes}")
        lines.append("")

    if m:
        lines.extend([
            "## Metrics",
            "",
            "| Metric | Precision | Recall |",
            "|--------|-----------|--------|",
            f"| Act (create) | {m['act']['precision']} | {m['act']['recall']} |",
            f"| Verify (clarify) | {m['verify']['precision']} | {m['verify']['recall']} |",
            f"| Intent (detect) | {m['intent']['precision']} | {m['intent']['recall']} |",
            "",
        ])

    # Latency table
    lat = result.get("latency", {})
    if lat:
        lines.extend([
            "## Latency (ms)",
            "",
            "| p50 | p95 | mean | max |",
            "|-----|-----|------|-----|",
            f"| {lat['p50']} | {lat['p95']} | {lat['mean']} | {lat['max']} |",
            "",
        ])

    # Per-language breakdown
    by_lang = result.get("by_language", {})
    if by_lang:
        lines.extend([
            "## Per-Language",
            "",
            "| Language | Passed | Total | Pass % | Latency p50 | Latency p95 |",
            "|----------|--------|-------|--------|-------------|-------------|",
        ])
        for lang in sorted(by_lang):
            d = by_lang[lang]
            l = d.get("latency", {})
            lines.append(f"| {lang} | {d['passed']} | {d['total']} | {d['pass_rate']}% | {l.get('p50', 0)} | {l.get('p95', 0)} |")
        lines.append("")

    # Per-stratum breakdown
    by_stratum = result.get("by_stratum", {})
    if by_stratum:
        lines.extend([
            "## Per-Stratum",
            "",
            "| Stratum | Passed | Total | Pass % |",
            "|---------|--------|-------|--------|",
        ])
        for stratum in sorted(by_stratum):
            d = by_stratum[stratum]
            lines.append(f"| {stratum} | {d['passed']} | {d['total']} | {d['pass_rate']}% |")
        lines.append("")

    if result["failures"]:
        lines.extend([
            f"## Failures ({len(result['failures'])})",
            "",
        ])
        for fail in result["failures"]:
            lines.append(f"### {fail['id']}")
            lines.append(f"**Input:** `{fail['input_text']}`")
            lines.append("")
            r = fail["result"]
            failed_checks = [k for k, v in r.items() if k != "passed" and not v]
            lines.append(f"**Failed checks:** {', '.join(failed_checks)}")
            lines.append("")
            pred = fail["predicted"]
            if pred.get("reminder"):
                lines.append(f"- **what:** `{pred['reminder']['what']}`")
                lines.append(f"- **when:** `{pred['reminder']['when']}`")
            if pred.get("clarification_question"):
                lines.append(f"- **question:** `{pred['clarification_question']}`")
            lines.append(f"- **status:** `{pred['status']}`")
            lines.append(f"- **missing_fields:** `{pred['missing_fields']}`")
            lines.append("")
    else:
        lines.extend(["## Failures", "", "None — all cases passed.", ""])

    with md_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return md_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", type=str, default="test",
                        help="Split to run: train, val, or test (default: test)")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--conversations", action="store_true",
                        help="Run conversation replay fixtures instead of row-based splits")
    parser.add_argument("--conversations-dir", type=Path, default=DEFAULT_CONVERSATIONS_DIR)
    parser.add_argument("--quiet", action="store_true", help="Only print summary")
    parser.add_argument("--notes", type=str, default=None, help="Notes to include in report")
    parser.add_argument("--runs-dir", type=Path, default=RUNS_DIR)
    args = parser.parse_args()

    run_id = generate_run_id()
    run_dir = args.runs_dir / run_id

    if args.conversations:
        conv_dir = args.conversations_dir
        if not conv_dir.exists():
            print(f"No conversations found at {conv_dir}")
            raise SystemExit(1)
        conv_files = sorted(conv_dir.glob("*.jsonl"))
        if not conv_files:
            print(f"No conversation fixtures in {conv_dir}")
            raise SystemExit(1)

        print(f"Run ID: {run_id}")
        print(f"Mode: conversations ({len(conv_files)} fixtures)")
        print()

        all_results = []
        total_passed = 0
        total_cases = 0
        all_failures = []
        all_latencies = []
        all_per_case = []
        lang_pass: dict[str, list[bool]] = {}
        lang_latency: dict[str, list[float]] = {}

        for conv_path in conv_files:
            print(f"  Running: {conv_path.name}")
            result = run_conversation(conv_path, verbose=not args.quiet)
            total_passed += result["passed"]
            total_cases += result["total"]
            all_failures.extend(result["failures"])
            all_latencies.extend([c.get("predicted", {}).get("timings", {}).get("total_ms", 0) for c in result["per_case"]])
            all_per_case.extend(result["per_case"])
            for lang, d in result.get("by_language", {}).items():
                lang_pass.setdefault(lang, []).extend([c["passed"] for c in result["per_case"] if c.get("language") == lang])
                lang_latency.setdefault(lang, []).extend([c.get("predicted", {}).get("timings", {}).get("total_ms", 0) for c in result["per_case"] if c.get("language") == lang])
            if result["failures"] and not args.quiet:
                for fail in result["failures"]:
                    print(f"    FAIL: {fail['id']}: {[k for k,v in fail['result'].items() if k != 'passed' and not v]}")

        combined = {
            "total": total_cases,
            "passed": total_passed,
            "metrics": {},
            "failures": all_failures,
            "per_case": all_per_case,
            "latency": _percentiles(all_latencies),
            "by_language": {lang: {
                "passed": sum(results),
                "total": len(results),
                "pass_rate": round(sum(results) / len(results) * 100, 1) if results else 0,
                "latency": _percentiles(lang_latency.get(lang, [])),
            } for lang, results in lang_pass.items()},
            "by_stratum": {},
        }

        md_path = write_report(run_id, run_dir, "conversations", combined, notes=args.notes)

        print(f"\n{'=' * 50}")
        print(f"Conversations: {total_passed}/{total_cases} passed")
        print(f"{'=' * 50}")
        lat = combined["latency"]
        print(f"  Latency: p50={lat['p50']}ms p95={lat['p95']}ms mean={lat['mean']}ms max={lat['max']}ms")
        if all_failures and not args.quiet:
            print(f"\n  Failures ({len(all_failures)}):")
            for fail in all_failures:
                print(f"    {fail['id']}: {[k for k,v in fail['result'].items() if k != 'passed' and not v]}")
        print(f"\n  Report saved: {md_path}")
        print(f"  Raw JSON:     {run_dir / 'conversations.json'}")

        if total_passed != total_cases:
            raise SystemExit(1)
        return

    path = args.data_dir / f"{args.split}.jsonl"
    if not path.exists():
        print(f"No eval data found at {path}")
        raise SystemExit(1)

    print(f"Run ID: {run_id}")
    print(f"Split: {args.split}")
    print()

    result = run_split(path, verbose=not args.quiet)

    md_path = write_report(run_id, run_dir, args.split, result, notes=args.notes)

    print(f"\n{'=' * 50}")
    print(f"Split: {args.split} ({path})")
    print(f"{'=' * 50}")
    print(f"  Passed: {result['passed']}/{result['total']}")

    if result["metrics"]:
        m = result["metrics"]
        print(f"\n  Metrics:")
        print(f"    Act (create):     precision={m['act']['precision']} recall={m['act']['recall']}")
        print(f"    Verify (clarify): precision={m['verify']['precision']} recall={m['verify']['recall']}")
        print(f"    Intent (detect):  precision={m['intent']['precision']} recall={m['intent']['recall']}")

    lat = result.get("latency", {})
    if lat:
        print(f"\n  Latency: p50={lat['p50']}ms p95={lat['p95']}ms mean={lat['mean']}ms max={lat['max']}ms")

    by_lang = result.get("by_language", {})
    if by_lang:
        print(f"\n  Per-Language:")
        for lang in sorted(by_lang):
            d = by_lang[lang]
            l = d.get("latency", {})
            print(f"    {lang}: {d['passed']}/{d['total']} ({d['pass_rate']}%) p50={l.get('p50', 0)}ms")

    by_stratum = result.get("by_stratum", {})
    if by_stratum:
        print(f"\n  Per-Stratum:")
        for stratum in sorted(by_stratum):
            d = by_stratum[stratum]
            print(f"    {stratum}: {d['passed']}/{d['total']} ({d['pass_rate']}%)")

    if result["failures"] and not args.quiet:
        print(f"\n  Failures ({len(result['failures'])}):")
        for fail in result["failures"]:
            print(f"    {fail['id']}: {[k for k,v in fail['result'].items() if k != 'passed' and not v]}")

    print(f"\n  Report saved: {md_path}")
    print(f"  Raw JSON:     {run_dir / f'{args.split}.json'}")

    if result["passed"] != result["total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
