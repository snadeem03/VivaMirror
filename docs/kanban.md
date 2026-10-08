# VivaMirror — Kanban (local mirror)

Sprint: **Sprint 1 — Accelerated student development sprint** (see `docs/sprint_backlog.md`).
Sprint start: 2026-10-09T00:14:05+05:30 (Asia/Kolkata).
Remote mirror: GitHub Project board — **not created yet** (blocked on `gh` auth;
see `docs/sprint_backlog.md` §7 analogue / final report). This file is the source
of truth until the remote board exists. Do not claim the remote board exists.

## WIP rule

- **Maximum 1 implementation story in In Progress at any time** (single developer).
- Planning/process cards do not count against the WIP limit.

## Board (real status as of Milestone 0 commit — no implementation started)

### Done

| Card | Note |
|------|------|
| M0 — Project init + Agile planning | Planning artifacts committed (`README`, backlog, sprint, kanban, events, architecture, demo plan, `.gitignore`); satisfies US-14 planning portion |

### Review

*(empty — nothing awaiting review; self-review happens per story during the sprint)*

### In Progress

*(empty — 0 implementation stories in progress; WIP limit respected)*

### Ready (committed sprint scope — pull one at a time, in this order)

| Card | Estimate |
|------|----------|
| US-10 — Curated 15-Q rubric bank | 60 min |
| US-06 — Rubric evaluation + evidence, negation-safe | 60 min |
| US-02 — Typed-answer mode | 25 min |
| US-05 — Review/edit before evaluation | 20 min |
| US-01 — Question select | 20 min |
| US-08 — SQLite history + progress | 35 min |
| US-07 — Retry + compare | 30 min |
| US-09 — Streamlit end-to-end flow | 40 min |
| US-11 (incremental) — guardrails in code | 5 min |

### Backlog (stretch / out of committed scope)

| Card | Estimate |
|------|----------|
| US-03/US-04 (spike) — Audio record/upload + adapter stub | 30 min timebox |
| US-12 — Meaningful tests, CI-safe | 40 min |
| US-14 (remainder) — GitHub Issues + Project board | 25 min |
| US-13 — CI + versioned archive workflows | 30 min |
| US-15 — Follow-up prompts | 15 min |
| US-16 — Progress charts polish | 20 min |

## When a card can move to Done (card-level Definition of Done)

1. All acceptance criteria for the story verified (hand-check or test).
2. WIP rule was respected while it was In Progress.
3. No secrets, raw audio, or generated DB files in the change (`git status` checked).
4. A `docs/progress_events.jsonl` event was appended for start **and** completion
   (ISO timestamp + timezone, story ID, remaining-minutes estimate).
5. The end-to-end practice loop still works after the change.
6. No new claims that coverage measures correctness, confidence, intelligence,
   or speaking ability; no raw-audio retention introduced.

Move order: Backlog → Ready (at sprint planning only) → In Progress (max 1)
→ Review (self-review + tests pass) → Done. Reopened cards return to Ready with
a new progress event explaining why.
