"""Generate stratified example cases for the reminder agent eval.

Produces train.jsonl, val.jsonl, test.jsonl in data/examples/.

Usage:
    python scripts/generate_examples.py
    python scripts/generate_examples.py --seed 42
    python scripts/generate_examples.py --train 200 --val 50 --test 50
"""
from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

TZ = timezone(timedelta(hours=3))
BASE_TIME = datetime(2026, 7, 10, 0, 51, 0, tzinfo=TZ)
# Late-night anchor for day-rollover testing
LATE_NIGHT_TIME = datetime(2026, 7, 10, 23, 55, 0, tzinfo=TZ)

# Pool of current_time anchors for varied relative-time testing
TIME_ANCHORS = [BASE_TIME, LATE_NIGHT_TIME]

OUTPUT_DIR = Path("data/examples")

# ---------------------------------------------------------------------------
# Variation pools
# ---------------------------------------------------------------------------

INTENT_PHRASINGS = [
    "remind me {date} {time} to {task}",
    "remind me {date} at {time} to {task}",
    "remind me {time} {date} to {task}",
    "remind me to {task} {date} {time}",
    "remind me to {task} {date} at {time}",
    "don't forget to {task} {date} {time}",
    "don't forget to {task} {date} at {time}",
    "don't forget {date} {time} to {task}",
    "make sure I {task} {date} {time}",
    "make sure I {task} {date} at {time}",
    "remind me that I need to {task} {date} {time}",
    "I need a reminder to {task} {date} {time}",
]

INTENT_PHRASINGS_NO_TIME = [
    "remind me {date} to {task}",
    "remind me to {task} {date}",
    "don't forget to {task} {date}",
    "don't forget {date} to {task}",
    "make sure I {task} {date}",
    "remind me that I need to {task} {date}",
    "I need a reminder to {task} {date}",
]

INTENT_PHRASINGS_NO_DATE = [
    "remind me at {time} to {task}",
    "remind me {time} to {task}",
    "don't forget to {task} at {time}",
    "don't forget at {time} to {task}",
    "make sure I {task} at {time}",
    "I need a reminder to {task} at {time}",
]

INTENT_PHRASINGS_NO_BOTH = [
    "remind me to {task}",
    "don't forget to {task}",
    "make sure I {task}",
    "remind me that I need to {task}",
    "I need a reminder to {task}",
]

INTENT_PHRASINGS_NO_TASK = [
    "remind me {date} {time}",
    "remind me {date} at {time}",
    "don't forget {date} {time}",
    "make sure I remember {date} at {time}",
]

TASKS = [
    "call dad", "call mom", "call the dentist", "call the doctor",
    "buy milk", "buy groceries", "buy a birthday gift",
    "submit the report", "submit the application", "submit the invoice",
    "pick up the kids", "pick up the dry cleaning", "pick up the package",
    "send the email", "send the invoice", "send the documents",
    "take medication", "take the car to the mechanic",
    "water the plants", "feed the cat", "walk the dog",
    "renew the subscription", "pay the electric bill", "pay the rent",
    "schedule a meeting", "book a flight", "reserve a table",
    "finish the presentation", "review the contract", "update the resume",
]

# Hebrew tasks
HE_TASKS = [
    "להתקשר לאבא", "להתקשר לאמא", "לקנות חלב", "לקנות מצרכים",
    "לשלוח את הדוח", "לשלוח את החשבונית", "לאסוף את הילדים",
    "לקחת תרופות", "להשקות את הצמחים", "להאכיל את החתול",
    "לטייל עם הכלב", "לחדש את המנוי", "לשלם את חשבון החשמל",
    "לשלם את השכירות", "לסיים את המצגת", "לבדוק את החוזה",
    "לעשן", "לשתות תה", "לנוח", "לקרוא ספר",
]

# July 10, 2026 is a Friday. Offsets are relative to that date.
DATE_EXPRS = [
    ("today", 0),
    ("tomorrow", 1),
    ("on monday", 3),       # Jul 13
    ("on tuesday", 4),      # Jul 14
    ("on wednesday", 5),    # Jul 15
    ("on thursday", 6),     # Jul 16
    ("on friday", 7),       # Jul 17 (next Friday, today is Friday)
    ("on saturday", 1),     # Jul 11
    ("on sunday", 2),       # Jul 12
    ("this monday", 3),     # Jul 13 (coming Monday)
    ("this friday", 0),     # Jul 10 (today)
    ("next monday", 3),     # Jul 13 (nearest upcoming Monday)
    ("next friday", 7),     # Jul 17 (7 days from today)
]

TIME_EXPRS = [
    ("3pm", 15, 0),
    ("3 pm", 15, 0),
    ("9am", 9, 0),
    ("9 am", 9, 0),
    ("15:00", 15, 0),
    ("09:00", 9, 0),
    ("10:30", 10, 30),
    ("3:30 pm", 15, 30),
    ("9:00 am", 9, 0),
    ("noon", 12, 0),
    ("midnight", 0, 0),
    ("8am", 8, 0),
    ("8 am", 8, 0),
    ("6pm", 18, 0),
    ("6 pm", 18, 0),
    ("7:45 am", 7, 45),
    ("11:15", 11, 15),
    ("4:45 pm", 16, 45),
]

# Relative-time expressions: (expression, offset_seconds, language)
# These are self-contained — they fix both date and time.
RELATIVE_TIME_EXPRS = [
    ("in a minute", 60, "en"),
    ("in 5 minutes", 300, "en"),
    ("in 10 minutes", 600, "en"),
    ("in 30 minutes", 1800, "en"),
    ("in an hour", 3600, "en"),
    ("in 2 hours", 7200, "en"),
    ("in half an hour", 1800, "en"),
    ("עוד דקה", 60, "he"),
    ("עוד 5 דקות", 300, "he"),
    ("עוד 10 דקות", 600, "he"),
    ("עוד חצי שעה", 1800, "he"),
    ("עוד שעה", 3600, "he"),
    ("עוד שעתיים", 7200, "he"),
    ("בעוד חצי שעה", 1800, "he"),
]

# Hebrew intent phrasings
HE_INTENT_PHRASINGS = [
    "תזכיר לי {date} {time} {task}",
    "תזכיר לי {date} ב-{time} {task}",
    "תזכיר לי {time} {date} {task}",
    "תזכיר לי {task} {date} {time}",
    "תזכיר לי {task} {date} ב-{time}",
    "אל תשכח {task} {date} {time}",
    "אל תשכח {date} {time} {task}",
    "תזכיר לי שאני צריך {task} {date} {time}",
]

HE_INTENT_PHRASINGS_NO_TIME = [
    "תזכיר לי {date} {task}",
    "תזכיר לי {task} {date}",
    "אל תשכח {task} {date}",
    "אל תשכח {date} {task}",
    "תזכיר לי שאני צריך {task} {date}",
]

HE_INTENT_PHRASINGS_NO_DATE = [
    "תזכיר לי ב-{time} {task}",
    "תזכיר לי {time} {task}",
    "אל תשכח {task} ב-{time}",
]

HE_INTENT_PHRASINGS_NO_BOTH = [
    "תזכיר לי {task}",
    "אל תשכח {task}",
    "תזכיר לי שאני צריך {task}",
]

HE_DATE_EXPRS = [
    ("היום", 0),
    ("מחר", 1),
    ("ביום שני", 3),
    ("ביום שלישי", 4),
    ("ביום רביעי", 5),
    ("ביום חמישי", 6),
    ("ביום שישי", 7),
    ("ביום שבת", 1),
    ("ביום ראשון", 2),
]

HE_TIME_EXPRS = [
    ("3 בצהריים", 15, 0),
    ("9 בבוקר", 9, 0),
    ("15:00", 15, 0),
    ("09:00", 9, 0),
    ("10:30", 10, 30),
    ("12:00", 12, 0),
    ("8 בבוקר", 8, 0),
    ("6 בערב", 18, 0),
    ("7:45", 7, 45),
]

HE_IRRELEVANT_INPUTS = [
    "מה מזג האוויר היום",
    "ספר לי בדיחה",
    "מה שלומך",
    "כמה השעה",
    "מה בירת צרפת",
    "תשיר שיר",
    "מה החדשות היום",
    "איך מגיעים לשדה התעופה",
    "מה כדאי לאכול לארוחת ערב",
    "תמליץ לי על ספר",
]

IRRELEVANT_INPUTS = [
    "what's the weather today",
    "tell me a joke",
    "how are you doing",
    "what time is it",
    "who won the game last night",
    "what's the capital of France",
    "can you sing a song",
    "translate hello to Spanish",
    "what movies are playing",
    "play some music",
    "what's the news today",
    "how do I get to the airport",
    "what's 2 plus 2",
    "tell me about quantum physics",
    "what's your favorite color",
    "can you write a poem",
    "what's the stock price of Apple",
    "how tall is Mount Everest",
    "what's for dinner tonight",
    "recommend a good book",
    "what's the meaning of life",
    "how do I bake a cake",
    "what's the exchange rate for euros",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def resolve_date(date_expr: str, offset_days: int) -> datetime:
    return BASE_TIME + timedelta(days=offset_days)


def resolve_time(hour: int, minute: int) -> timedelta:
    return timedelta(hours=hour, minutes=minute)


def make_when(date_offset: int, hour: int, minute: int) -> str:
    date_part = (BASE_TIME + timedelta(days=date_offset)).date()
    dt = datetime.combine(date_part, datetime.min.time().replace(hour=hour, minute=minute), tzinfo=TZ)
    return dt.isoformat()


def make_when_from_anchor(anchor: datetime, offset_seconds: int) -> str:
    """Compute resolved datetime from a time anchor + offset (for relative times)."""
    return (anchor + timedelta(seconds=offset_seconds)).isoformat()


def make_id(prefix: str, idx: int) -> str:
    return f"{prefix}_{idx:04d}"


def format_phrase(template: str, task: str, date: str = "", time: str = "") -> str:
    return template.format(task=task, date=date, time=time).strip()


# ---------------------------------------------------------------------------
# Generators per decision space
# ---------------------------------------------------------------------------

def gen_created(n: int, rng: random.Random) -> list[dict]:
    cases = []
    for i in range(n):
        template = rng.choice(INTENT_PHRASINGS)
        task = rng.choice(TASKS)
        date_expr, date_offset = rng.choice(DATE_EXPRS)
        time_expr, hour, minute = rng.choice(TIME_EXPRS)
        text = format_phrase(template, task, date_expr, time_expr)
        when = make_when(date_offset, hour, minute)
        cases.append({
            "id": make_id("created", i),
            "language": "en",
            "input": {
                "input_id": f"msg-{i:04d}",
                "text": text,
                "current_time": BASE_TIME.isoformat(),
                "prior_context": None,
            },
            "expected": {
                "status": "created",
                "missing_fields": [],
                "reminder_what": task,
                "reminder_when": when,
                "clarification_keywords": [],
            },
        })
    return cases


def gen_missing_time(n: int, rng: random.Random) -> list[dict]:
    cases = []
    for i in range(n):
        template = rng.choice(INTENT_PHRASINGS_NO_TIME)
        task = rng.choice(TASKS)
        date_expr, _ = rng.choice(DATE_EXPRS)
        text = format_phrase(template, task, date_expr)
        cases.append({
            "id": make_id("miss_time", i),
            "language": "en",
            "input": {
                "input_id": f"msg-{i:04d}",
                "text": text,
                "current_time": BASE_TIME.isoformat(),
                "prior_context": None,
            },
            "expected": {
                "status": "needs_clarification",
                "missing_fields": ["time"],
                "reminder_what": None,
                "reminder_when": None,
                "clarification_keywords": ["time", task],
            },
        })
    return cases


def gen_missing_date(n: int, rng: random.Random) -> list[dict]:
    cases = []
    for i in range(n):
        template = rng.choice(INTENT_PHRASINGS_NO_DATE)
        task = rng.choice(TASKS)
        time_expr, _, _ = rng.choice(TIME_EXPRS)
        text = format_phrase(template, task, time=time_expr)
        cases.append({
            "id": make_id("miss_date", i),
            "language": "en",
            "input": {
                "input_id": f"msg-{i:04d}",
                "text": text,
                "current_time": BASE_TIME.isoformat(),
                "prior_context": None,
            },
            "expected": {
                "status": "needs_clarification",
                "missing_fields": ["date"],
                "reminder_what": None,
                "reminder_when": None,
                "clarification_keywords": ["date", task],
            },
        })
    return cases


def gen_missing_both(n: int, rng: random.Random) -> list[dict]:
    cases = []
    for i in range(n):
        template = rng.choice(INTENT_PHRASINGS_NO_BOTH)
        task = rng.choice(TASKS)
        text = format_phrase(template, task)
        cases.append({
            "id": make_id("miss_both", i),
            "language": "en",
            "input": {
                "input_id": f"msg-{i:04d}",
                "text": text,
                "current_time": BASE_TIME.isoformat(),
                "prior_context": None,
            },
            "expected": {
                "status": "needs_clarification",
                "missing_fields": ["date", "time"],
                "reminder_what": None,
                "reminder_when": None,
                "clarification_keywords": [task],
            },
        })
    return cases


def gen_ignored(n: int, rng: random.Random) -> list[dict]:
    cases = []
    for i in range(n):
        text = rng.choice(IRRELEVANT_INPUTS)
        cases.append({
            "id": make_id("ignored", i),
            "language": "en",
            "input": {
                "input_id": f"msg-{i:04d}",
                "text": text,
                "current_time": BASE_TIME.isoformat(),
                "prior_context": None,
            },
            "expected": {
                "status": "ignored",
                "missing_fields": [],
                "reminder_what": None,
                "reminder_when": None,
                "clarification_keywords": [],
            },
        })
    return cases


def gen_multi_turn(n: int, rng: random.Random) -> list[dict]:
    cases = []
    for i in range(n):
        task = rng.choice(TASKS)
        date_expr, date_offset = rng.choice(DATE_EXPRS)
        time_expr, hour, minute = rng.choice(TIME_EXPRS)
        when = make_when(date_offset, hour, minute)

        # Decide what the user provides in turn 2
        turn_type = rng.choice(["time", "date"])

        if turn_type == "time":
            turn1_text = f"remind me {date_expr} to {task}"
            agent_q = f"What time should I remind you to {task}?"
            turn2_text = time_expr
            expected_status = "created"
            expected_missing = []
            expected_what = task
            expected_when = when
            expected_keywords = []
        else:
            turn1_text = f"remind me at {time_expr} to {task}"
            agent_q = f"What day should I remind you to {task}?"
            turn2_text = date_expr
            expected_status = "created"
            expected_missing = []
            expected_what = task
            expected_when = when
            expected_keywords = []

        cases.append({
            "id": make_id(f"multi_{turn_type}", i),
            "input": {
                "input_id": f"msg-{i:04d}",
                "text": turn2_text,
                "current_time": (BASE_TIME + timedelta(seconds=30)).isoformat(),
                "prior_context": [
                    {"role": "user", "text": turn1_text},
                    {"role": "agent", "text": agent_q},
                ],
            },
            "expected": {
                "status": expected_status,
                "missing_fields": expected_missing,
                "reminder_what": expected_what,
                "reminder_when": expected_when,
                "clarification_keywords": expected_keywords,
            },
        })
    return cases


def gen_edge_cases(n: int, rng: random.Random) -> list[dict]:
    cases = []
    for i in range(n):
        template = rng.choice(INTENT_PHRASINGS_NO_TASK)
        date_expr, _ = rng.choice(DATE_EXPRS)
        time_expr, _, _ = rng.choice(TIME_EXPRS)
        text = format_phrase(template, task="", date=date_expr, time=time_expr)
        cases.append({
            "id": make_id("edge_no_task", i),
            "language": "en",
            "input": {
                "input_id": f"msg-{i:04d}",
                "text": text,
                "current_time": BASE_TIME.isoformat(),
                "prior_context": None,
            },
            "expected": {
                "status": "needs_clarification",
                "missing_fields": ["task"],
                "reminder_what": None,
                "reminder_when": None,
                "clarification_keywords": [],
            },
        })
    return cases


def gen_he_created(n: int, rng: random.Random) -> list[dict]:
    cases = []
    for i in range(n):
        template = rng.choice(HE_INTENT_PHRASINGS)
        task = rng.choice(HE_TASKS)
        date_expr, date_offset = rng.choice(HE_DATE_EXPRS)
        time_expr, hour, minute = rng.choice(HE_TIME_EXPRS)
        text = format_phrase(template, task, date_expr, time_expr)
        when = make_when(date_offset, hour, minute)
        cases.append({
            "id": make_id("he_created", i),
            "language": "he",
            "input": {
                "input_id": f"msg-{i:04d}",
                "text": text,
                "current_time": BASE_TIME.isoformat(),
                "prior_context": None,
            },
            "expected": {
                "status": "created",
                "missing_fields": [],
                "reminder_what": task,
                "reminder_when": when,
                "clarification_keywords": [],
            },
        })
    return cases


def gen_he_missing_time(n: int, rng: random.Random) -> list[dict]:
    cases = []
    for i in range(n):
        template = rng.choice(HE_INTENT_PHRASINGS_NO_TIME)
        task = rng.choice(HE_TASKS)
        date_expr, _ = rng.choice(HE_DATE_EXPRS)
        text = format_phrase(template, task, date_expr)
        cases.append({
            "id": make_id("he_miss_time", i),
            "language": "he",
            "input": {
                "input_id": f"msg-{i:04d}",
                "text": text,
                "current_time": BASE_TIME.isoformat(),
                "prior_context": None,
            },
            "expected": {
                "status": "needs_clarification",
                "missing_fields": ["time"],
                "reminder_what": None,
                "reminder_when": None,
                "clarification_keywords": ["time", task],
            },
        })
    return cases


def gen_he_missing_date(n: int, rng: random.Random) -> list[dict]:
    cases = []
    for i in range(n):
        template = rng.choice(HE_INTENT_PHRASINGS_NO_DATE)
        task = rng.choice(HE_TASKS)
        time_expr, _, _ = rng.choice(HE_TIME_EXPRS)
        text = format_phrase(template, task, time=time_expr)
        cases.append({
            "id": make_id("he_miss_date", i),
            "language": "he",
            "input": {
                "input_id": f"msg-{i:04d}",
                "text": text,
                "current_time": BASE_TIME.isoformat(),
                "prior_context": None,
            },
            "expected": {
                "status": "needs_clarification",
                "missing_fields": ["date"],
                "reminder_what": None,
                "reminder_when": None,
                "clarification_keywords": ["date", task],
            },
        })
    return cases


def gen_he_ignored(n: int, rng: random.Random) -> list[dict]:
    cases = []
    for i in range(n):
        text = rng.choice(HE_IRRELEVANT_INPUTS)
        cases.append({
            "id": make_id("he_ignored", i),
            "language": "he",
            "input": {
                "input_id": f"msg-{i:04d}",
                "text": text,
                "current_time": BASE_TIME.isoformat(),
                "prior_context": None,
            },
            "expected": {
                "status": "ignored",
                "missing_fields": [],
                "reminder_what": None,
                "reminder_when": None,
                "clarification_keywords": [],
            },
        })
    return cases


def gen_relative_time(n: int, rng: random.Random) -> list[dict]:
    """Relative-time created cases in EN + HE with varied anchors."""
    cases = []
    for i in range(n):
        rel_expr, offset_sec, lang = rng.choice(RELATIVE_TIME_EXPRS)
        anchor = rng.choice(TIME_ANCHORS)
        if lang == "he":
            task = rng.choice(HE_TASKS)
            text = f"תזכיר לי {rel_expr} {task}"
        else:
            task = rng.choice(TASKS)
            text = f"remind me {rel_expr} to {task}"
        when = make_when_from_anchor(anchor, offset_sec)
        cases.append({
            "id": make_id("rel_time", i),
            "language": lang,
            "input": {
                "input_id": f"msg-{i:04d}",
                "text": text,
                "current_time": anchor.isoformat(),
                "prior_context": None,
            },
            "expected": {
                "status": "created",
                "missing_fields": [],
                "reminder_what": task,
                "reminder_when": when,
                "reminder_when_tolerance_seconds": 90,
                "clarification_keywords": [],
            },
        })
    return cases


def gen_multi_turn_relative(n: int, rng: random.Random) -> list[dict]:
    """Multi-turn where turn 2 is a relative-time answer."""
    cases = []
    for i in range(n):
        rel_expr, offset_sec, lang = rng.choice(RELATIVE_TIME_EXPRS)
        anchor = rng.choice(TIME_ANCHORS)
        if lang == "he":
            task = rng.choice(HE_TASKS)
            turn1 = f"תזכיר לי היום {task}"
            agent_q = f"באיזו שעה להזכיר לך {task}?"
        else:
            task = rng.choice(TASKS)
            turn1 = f"remind me today to {task}"
            agent_q = f"What time should I remind you to {task}?"
        when = make_when_from_anchor(anchor + timedelta(seconds=30), offset_sec)
        cases.append({
            "id": make_id("multi_rel", i),
            "language": lang,
            "input": {
                "input_id": f"msg-{i:04d}",
                "text": rel_expr,
                "current_time": (anchor + timedelta(seconds=30)).isoformat(),
                "prior_context": [
                    {"role": "user", "text": turn1},
                    {"role": "agent", "text": agent_q},
                ],
            },
            "expected": {
                "status": "created",
                "missing_fields": [],
                "reminder_what": task,
                "reminder_when": when,
                "reminder_when_tolerance_seconds": 90,
                "clarification_keywords": [],
            },
        })
    return cases


# ---------------------------------------------------------------------------
# Stratification config
# ---------------------------------------------------------------------------

STRATA = [
    ("created", gen_created),
    ("missing_time", gen_missing_time),
    ("missing_date", gen_missing_date),
    ("missing_both", gen_missing_both),
    ("ignored", gen_ignored),
    ("multi_turn", gen_multi_turn),
    ("edge", gen_edge_cases),
    ("he_created", gen_he_created),
    ("he_missing_time", gen_he_missing_time),
    ("he_missing_date", gen_he_missing_date),
    ("he_ignored", gen_he_ignored),
    ("relative_time", gen_relative_time),
    ("multi_turn_relative", gen_multi_turn_relative),
]

# Default counts per stratum per split
DEFAULT_SPLITS = {
    "train": {"created": 20, "missing_time": 12, "missing_date": 12, "missing_both": 12,
              "ignored": 12, "multi_turn": 8, "edge": 4,
              "he_created": 10, "he_missing_time": 6, "he_missing_date": 6, "he_ignored": 6,
              "relative_time": 10, "multi_turn_relative": 6},
    "val":   {"created": 6,  "missing_time": 3,  "missing_date": 3,  "missing_both": 3,
              "ignored": 3,  "multi_turn": 3, "edge": 2,
              "he_created": 4,  "he_missing_time": 2, "he_missing_date": 2, "he_ignored": 2,
              "relative_time": 4, "multi_turn_relative": 3},
    "test":  {"created": 6,  "missing_time": 3,  "missing_date": 3,  "missing_both": 3,
              "ignored": 3,  "multi_turn": 3, "edge": 2,
              "he_created": 4,  "he_missing_time": 2, "he_missing_date": 2, "he_ignored": 2,
              "relative_time": 4, "multi_turn_relative": 3},
}


def generate_split(split_name: str, counts: dict, rng: random.Random) -> list[dict]:
    cases = []
    for stratum_name, gen_fn in STRATA:
        n = counts.get(stratum_name, 0)
        if n > 0:
            cases.extend(gen_fn(n, rng))
    rng.shuffle(cases)
    return cases


def write_jsonl(path: Path, cases: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate stratified eval examples.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train", type=int, default=100, help="Target train count (distributed proportionally)")
    parser.add_argument("--val", type=int, default=30, help="Target val count")
    parser.add_argument("--test", type=int, default=30, help="Target test count")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    rng = random.Random(args.seed)

    # Scale counts proportionally if custom totals are given
    base_train = sum(DEFAULT_SPLITS["train"].values())
    base_val = sum(DEFAULT_SPLITS["val"].values())
    base_test = sum(DEFAULT_SPLITS["test"].values())

    def scale(counts: dict, target: int, base: int) -> dict:
        factor = target / base
        return {k: max(1, round(v * factor)) for k, v in counts.items()}

    splits = {
        "train": scale(DEFAULT_SPLITS["train"], args.train, base_train),
        "val": scale(DEFAULT_SPLITS["val"], args.val, base_val),
        "test": scale(DEFAULT_SPLITS["test"], args.test, base_test),
    }

    for split_name, counts in splits.items():
        cases = generate_split(split_name, counts, rng)
        path = args.output_dir / f"{split_name}.jsonl"
        write_jsonl(path, cases)

        # Print stratum breakdown
        breakdown = {}
        for case in cases:
            prefix = case["id"].rsplit("_", 1)[0]
            breakdown[prefix] = breakdown.get(prefix, 0) + 1

        print(f"{split_name}.jsonl: {len(cases)} examples")
        for k in sorted(breakdown):
            print(f"  {k}: {breakdown[k]}")
        print()


if __name__ == "__main__":
    main()
