# VivaMirror — Kanban (local mirror)

Sprint: **Sprint 1 — Accelerated student development sprint** (see `docs/sprint_backlog.md`).
Sprint start: 2026-10-09T00:14:05+05:30 (Asia/Kolkata).
Remote mirror: GitHub Project board — **required, to be created now that `gh`
auth works** (correction M1). Until its URL is verified below, this file is the
source of truth. Do not claim the remote board exists until verified.

Remote board URL: _(pending — fill in after verified creation)_

## WIP rule

- **Maximum 1 implementation story in In Progress at any time** (single developer).
- Planning/process cards do not count against the WIP limit.

## Board (real status as of correction M1 — no implementation started)

### Done

| Card | Note |
|------|------|
| M0 — Project init + Agile planning | Committed `f7ec919`; satisfies US-14 planning portion |
| Correction M1 — Prioritize Agile/CI deliverables | Re-planned scope (485 min), US-17 added, burndown plan; local commit (hash below) |

### Review

*(empty)*

### In Progress

*(empty — 0 implementation stories in progress; US-10 starts here in Milestone 1)*

### Ready (committed sprint scope — pull one at a time, in this order)

| Card | Estimate |
|------|----------|
| US-10 — Curated 15-Q bank | 60 min |
| US-06 — Rubric evaluation + evidence, negation-safe | 60 min |
| US-12 — Meaningful tests, CI-safe | 40 min |
| US-01 — Question select | 20 min |
| US-02 — Typed-answer mode | 25 min |
| US-05 — Review/edit before evaluation | 20 min |
| US-04 — Transcription adapter | 35 min |
| US-03 — Record/upload audio | 40 min |
| US-08 — SQLite history + progress | 35 min |
| US-07 — Retry + compare | 30 min |
| US-09 — Streamlit flow (trimmed) | 30 min |
| US-11 — Guardrails in code | 15 min |
| US-13 — GitHub Actions CI + archive | 30 min |
| US-14 — Tracking remainder (Issues + board) | 25 min |
| US-17 — Hourly burndown | 20 min |

### Backlog (deferred post-MVP)

| Card | Note |
|------|------|
| US-15 — Follow-up prompts (interactive) | Deferred; content ships in US-10 data |
| US-16 — Progress charts polish | Deferred; US-07 comparison is the committed view |

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
