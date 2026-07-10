# Policy Assumptions

Behavioral rules the agent follows. Each one is a decision we made — let's agree or adjust.

---

## 1. What counts as a "complete" reminder?

| # | Rule | Example | Current Behavior | Agree? |
|---|------|---------|------------------|--------|
| P1 | A reminder is **complete** only when all 3 fields are explicitly stated: **task + date + time**. | "remind me tomorrow at 3pm to call dad" → created | ✅ created | |
| P2 | **Missing time** → needs clarification, even if date is present. | "remind me tomorrow to call dad" → ask for time | needs_clarification, missing=["time"] | |
| P3 | **Missing date** → needs clarification, even if time is present. | "remind me at 3pm to call dad" → ask for date | needs_clarification, missing=["date"] | |
| P4 | **Missing both date and time** → needs clarification. | "remind me to call dad" → ask when | needs_clarification, missing=["date", "time"] | |
| P5 | **Missing task** → needs clarification, even if date+time are present. | "remind me tomorrow at 3pm" → ask what | needs_clarification, missing=["task"] | |

**Open question:** Should "remind me to call dad" (no date/time) default to anything, or always ask?

---

## 2. Date resolution rules

| # | Rule | Example (base: Fri Jul 10) | Resolved To | Agree? |
|---|------|----------------------------|-------------|--------|
| P6 | **"today"** = current date. | "today" | Jul 10 | |
| P7 | **"tomorrow"** = current date + 1. | "tomorrow" | Jul 11 | |
| P8 | **"this \<weekday\>"** = nearest occurrence, **including today**. | "this friday" (today is Friday) | Jul 10 | |
| P9 | **"next \<weekday\>"** = nearest upcoming occurrence (common usage). | "next monday" (today is Friday) | Jul 13 | ✅ |
| P10 | **"\<weekday\>" alone** = nearest **upcoming** occurrence, **excluding today**. | "on friday" (today is Friday) | Jul 17 | ✅ |
| P11 | **"next friday"** when today is Friday = Jul 17 (7 days from now, not today). | "next friday" | Jul 17 | ✅ |

**Open questions:**
- Should we support "in 3 days", "next week", "end of month"?

---

## 3. Time resolution rules

| # | Rule | Example | Resolved To | Agree? |
|---|------|---------|-------------|--------|
| P12 | **"3pm" / "3 pm" / "15:00"** all resolve to 15:00. | "3pm" | 15:00 | |
| P13 | **"noon"** = 12:00, **"midnight"** = 00:00. | "midnight" | 00:00 | |
| P14 | **"in an hour"** = current_time + 1 hour. Counts as both date AND time. | "in an hour" (from 00:51) | 01:51 on Jul 10 | |
| P15 | **"in 30 minutes"** = current_time + 30 min. Counts as both date AND time. | "in 30 minutes" | 01:21 on Jul 10 | |
| P16 | Relative time expressions **count as specifying both date and time** — no separate date needed. | "remind me in an hour to call dad" → complete | created | |

**Open questions:**
- Should "in an hour" when current time is 23:30 roll over to the next day? (Currently yes — LLM handles this)
- Should we support "tonight", "this evening", "morning" as vague time expressions?
- Is "remind me at midnight" → 00:00 of **today** or **tomorrow**? (Currently LLM decides — ambiguous)

---

## 4. Task extraction rules

| # | Rule | Example Input | Extracted Task | Agree? |
|---|------|---------------|----------------|--------|
| P17 | Strip leading phrases: "remind me to", "to", "don't forget to", "make sure I", "that I need to". | "remind me to call dad" | "call dad" | |
| P18 | If no action is specified, task is **empty**. | "remind me tomorrow at 3pm" | "" (empty) | |
| P19 | "remind me" / "don't forget" alone is **never** a valid task. | "remind me" | "" (empty) | |
| P20 | LLM placeholder outputs (e.g. "none", "not specified", parenthetical descriptions) are filtered out. | LLM returns "(leave blank)" | "" (empty) | |

**Open questions:**
- Should "make sure I call dad" → "call dad" or "make sure I call dad"? (Currently strips "make sure I")
- Should "remind me that I need to call dad" → "call dad" or "that I need to call dad"?
- How to handle multi-action: "remind me to call dad and buy milk"?

---

## 5. Clarification policy

| # | Rule | Example | Behavior | Agree? |
|---|------|---------|----------|--------|
| P21 | **Task missing** → ask "what" first, even if date/time also missing. | "remind me tomorrow at 3pm" | "What would you like me to remind you about?" | |
| P22 | **Task present, date/time missing** → ask only about missing date/time. | "remind me to call dad" | "When should I remind you to call dad?" | |
| P23 | **Multiple fields missing** → single question covering all missing fields. | "remind me to call dad" (no date/time) | "When should I remind you to call dad?" (covers both) | |
| P24 | Clarification question is **LLM-generated** in user's language. | Hebrew input | Hebrew question | |
| P25 | After a reminder is **created** or input is **ignored**, conversation context is **reset**. | CLI: created → next message starts fresh | prior_context = None | |

**Open questions:**
- P21: Should we ask for all missing fields at once ("What and when should I remind you?") instead of task-first?
- P23: Should we ask separate questions for date vs time, or one combined "when" question?
- P25: Should context persist after a created reminder for follow-up like "also remind me the day before"?

---

## 6. Language policy

| # | Rule | Example | Behavior | Agree? |
|---|------|---------|----------|--------|
| P26 | Language is detected from the **current message**, not from conversation history. | Turn 1 in English, turn 2 "3pm" → language may vary | Detected per-message | |
| P27 | If language detection fails → default to `"en"`. | LLM returns empty language | "en" | |
| P28 | Confirmation messages and clarification questions are generated **in the detected language**. | Hebrew input → Hebrew output | LLM-rendered in target language | |
| P29 | The eval dataset is **English-only**. Language handling is tested manually. | test.jsonl | All English examples | |

**Open questions:**
- P26: In multi-turn, should language be inherited from turn 1? (e.g. user spoke Hebrew in turn 1, says "3pm" in turn 2 — should agent respond in Hebrew?)
- P29: Should we add Hebrew/bilingual examples to the eval dataset?

---

## 7. Confidence values

| # | Scenario | Confidence | Agree? |
|---|----------|-----------|--------|
| P30 | Reminder created | 0.9 | |
| P31 | Missing date/time (task present) | 0.7 | |
| P32 | Missing task | 0.5 | |
| P33 | Unresolvable datetime | 0.6 | |
| P34 | Irrelevant input | LLM-reported (clamped 0–1) | |

**Open question:** Should confidence be LLM-derived instead of hardcoded?

---

## 8. Intent boundaries

| # | Input | Classified As | Agree? |
|---|-------|---------------|--------|
| P35 | "set an alarm for 7am" | reminder_request (task="alarm", time=7am, date=today if not specified) | ✅ |
| P36 | "set a timer for 10 minutes" | reminder_request (task="timer", relative time in 10 min) | ✅ |
| P37 | "what's the weather" | irrelevant | |
| P38 | "remind me to call dad" | reminder_request | |
| P39 | "3pm" (with prior context of agent asking for time) | clarification_answer | |
| P40 | "3pm" (no prior context) | reminder_request or irrelevant? (LLM decides) | |

**Open questions:**
- P40: "3pm" with no context — is this a reminder request or irrelevant? Currently LLM decides.
