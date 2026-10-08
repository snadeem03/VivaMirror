# VivaMirror — Kanban (local mirror)

Sprint: **Sprint 1 — Accelerated student development sprint** (see `docs/sprint_backlog.md`).
Sprint start: 2026-10-09T00:14:05+05:30 (Asia/Kolkata).
Remote mirror: GitHub Project board — **required, to be created now that `gh`
auth works** (correction M1). Until its URL is verified below, this file is the
source of truth. Do not claim the remote board exists until verified.

Remote board URL: https://github.com/users/snadeem03/projects/2 (verified
2026-10-09 ~00:36 IST — Status options Backlog/Ready/In Progress/Review/Done;
custom fields Priority, Estimate, Sprint; all 17 story issues added with
verified field values). Issues: https://github.com/snadeem03/VivaMirror/issues
(US-01…US-17 map to issues #1…#17; #10 closed as done).

## WIP rule

- **Maximum 1 implementation story in In Progress at any time** (single developer).
- Planning/process cards do not count against the WIP limit.

## Board (real status as of Milestone 3 — US-01/US-02/US-05 done)

### Done

| Card | Note |
|------|------|
| M0 — Project init + Agile planning | Committed `f7ec919`; satisfies US-14 planning portion |
| Correction M1 — Prioritize Agile/CI deliverables | Committed `764a04e`; scope re-baselined to 485 min, US-17 added |
| US-10 — Curated 15-Q bank | Done Milestone 1: 15 Qs / 60 concepts in `data/questions.json`, loader + validation, 30 pytest green |
| Rubric fix — Clarify CAP definitions | Committed `a1a7b61`; ds-15 corrected, other 14 inspected, bank re-validated |
| US-06 — Rubric evaluation + evidence, negation-safe | Done Milestone 2: `app/evaluation.py` + 35 tests, full suite 65/65; issue #6 closed |
| M3 slice 1 — flow helper + requirements split | Committed `eeaf712`; `app/flow.py` + 11 tests; runtime/dev deps split |
| US-01 — Question select | Done Milestone 3: 15 listed, stable IDs, reset-on-change; issue #1 closed |
| US-02 — Typed-answer mode | Done Milestone 3: labeled typed path, no audio APIs; issue #2 closed |
| US-05 — Review/edit before evaluation | Done Milestone 3: separate actions, blank rejection, edit invalidates; issue #5 closed |
| US-04 — Transcription adapter | Done Milestone 4: adapter + UI routing verified, real base.en check passed; issue #4 closed |
| US-03 — Record/upload audio | Done Milestone 4: mic + upload + transcribe→review→evaluate, session-only audio, typed independent; issue #3 closed |
| US-08 — SQLite history + progress | Done Milestone 5: local DB, explicit save, history + progress, schema docs; issue #8 closed |
| US-07 — Retry + compare | Done Milestone 5: same-question retry, pp deltas, newly/regressed, evidence inspection; issue #7 closed |
| US-09 — Streamlit end-to-end flow | Done Milestone 5: full loop reachable, no login; issue #9 closed |
| US-11 — Guardrails in code | Done Milestone 5: no-audio-retention verified, statements present, no login/tracking/paid API; issue #11 closed |

### Review (waiting / under review — not done)

| Card | Note |
|------|------|
| US-14 — Tracking remainder | Waiting on sprint-end evidence (CI runs, final burndown); board/issues verified; stays open, see issue #14 |

### In Progress (max 1)

*(empty — US-07 completed; Milestone 5 done, CI milestone next)*

### Ready (committed sprint scope — pull one at a time, in this order)

| Card | Estimate |
|------|----------|
| US-12 — Meaningful tests, CI-safe (bank+evaluator+flow+UI+store+history subtasks done, story open) | 40 min |
| US-13 — GitHub Actions CI + archive | 30 min |
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
