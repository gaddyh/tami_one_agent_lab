from __future__ import annotations

from src.agent_feature_template.schemas import ReminderOutput


SYNONYMS: dict[str, list[str]] = {
    "date": ["date", "day", "when"],
    "time": ["time", "when"],
    "when": ["when", "date", "day", "time"],
}


def _stem(word: str) -> str:
    """Simple stemming for keyword matching."""
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return word[: -len(suffix)]
    return word


def _phrase_match(keyword: str, text: str) -> bool:
    """Check if a keyword phrase matches text, tolerating word form and article changes."""
    if keyword in text:
        return True
    # Try stem of the full phrase
    if _stem(keyword) in text:
        return True
    # Split into content words and check each independently
    words = keyword.split()
    if len(words) > 1:
        content_words = [w for w in words if w not in ("a", "an", "the", "to", "me", "i")]
        if content_words:
            all_found = True
            for w in content_words:
                w_stem = _stem(w)
                if not (w in text or w_stem in text or w_stem + "ing" in text or w_stem + "ed" in text):
                    all_found = False
                    break
            if all_found:
                return True
    return False


def keyword_hit(text: str | None, expected_keywords: list[str]) -> bool:
    """Check if all expected keywords (or their synonyms/stems) appear in text."""
    if not expected_keywords:
        return True
    if not text:
        return False
    normalized = text.lower()
    for keyword in expected_keywords:
        kw = keyword.lower()
        synonyms = SYNONYMS.get(kw, [kw])
        matched = False
        for syn in synonyms:
            if _phrase_match(syn, normalized):
                matched = True
                break
        if not matched:
            return False
    return True


def score_output(predicted: ReminderOutput, expected: dict) -> dict:
    status_ok = predicted.status == expected.get("status")
    missing_fields_ok = set(predicted.missing_fields) == set(expected.get("missing_fields", []))

    reminder_what_ok = True
    reminder_when_ok = True
    clarification_ok = True

    if expected.get("status") == "created":
        if predicted.reminder:
            expected_what = expected.get("reminder_what", "")
            reminder_what_ok = (
                predicted.reminder.what.lower() == expected_what.lower()
                if expected_what
                else True
            )
            expected_when = expected.get("reminder_when", "")
            tolerance_seconds = expected.get("reminder_when_tolerance_seconds", 0)
            if expected_when:
                from datetime import datetime
                try:
                    expected_dt = datetime.fromisoformat(expected_when)
                    # Normalize: compare without timezone (strip tz from both)
                    pred_when = predicted.reminder.when
                    if pred_when.tzinfo is not None:
                        pred_when = pred_when.replace(tzinfo=None)
                    if expected_dt.tzinfo is not None:
                        expected_dt = expected_dt.replace(tzinfo=None)
                    if tolerance_seconds > 0:
                        diff = abs((pred_when - expected_dt).total_seconds())
                        reminder_when_ok = diff <= tolerance_seconds
                    else:
                        reminder_when_ok = pred_when == expected_dt
                except (ValueError, TypeError):
                    reminder_when_ok = False
        else:
            reminder_what_ok = False
            reminder_when_ok = False

    if expected.get("status") == "needs_clarification":
        clarification_ok = keyword_hit(
            predicted.clarification_question,
            expected.get("clarification_keywords", []),
        )

    passed = all([
        status_ok,
        missing_fields_ok,
        reminder_what_ok,
        reminder_when_ok,
        clarification_ok,
    ])

    return {
        "passed": passed,
        "status_ok": status_ok,
        "missing_fields_ok": missing_fields_ok,
        "reminder_what_ok": reminder_what_ok,
        "reminder_when_ok": reminder_when_ok,
        "clarification_ok": clarification_ok,
    }


def compute_precision_recall(
    predictions: list[dict],
) -> dict:
    """Compute precision/recall metrics across eval cases."""

    def pr(tp: int, fp: int, fn: int) -> dict:
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        return {"precision": round(precision, 3), "recall": round(recall, 3)}

    act_tp = sum(1 for p in predictions if p["predicted_status"] == "created" and p["expected_status"] == "created")
    act_fp = sum(1 for p in predictions if p["predicted_status"] == "created" and p["expected_status"] != "created")
    act_fn = sum(1 for p in predictions if p["predicted_status"] != "created" and p["expected_status"] == "created")

    verify_tp = sum(1 for p in predictions if p["predicted_status"] == "needs_clarification" and p["expected_status"] == "needs_clarification")
    verify_fp = sum(1 for p in predictions if p["predicted_status"] == "needs_clarification" and p["expected_status"] != "needs_clarification")
    verify_fn = sum(1 for p in predictions if p["predicted_status"] != "needs_clarification" and p["expected_status"] == "needs_clarification")

    intent_tp = sum(1 for p in predictions if p["predicted_status"] != "ignored" and p["expected_status"] != "ignored")
    intent_fp = sum(1 for p in predictions if p["predicted_status"] != "ignored" and p["expected_status"] == "ignored")
    intent_fn = sum(1 for p in predictions if p["predicted_status"] == "ignored" and p["expected_status"] != "ignored")

    return {
        "act": pr(act_tp, act_fp, act_fn),
        "verify": pr(verify_tp, verify_fp, verify_fn),
        "intent": pr(intent_tp, intent_fp, intent_fn),
    }
