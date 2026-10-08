# VivaMirror — Sprint Backlog

## Sprint label (explicit)

> **Sprint 1 — Accelerated student development sprint (tonight's MVP build).**
> This is the ONLY sprint in tonight's plan. The 30–60-minute implementation
> work packages (Milestones M1…) are **work packages within this single
> sprint**, not separate Scrum sprints.

- **Sprint start (actual):** 2026-10-09T00:14:05+05:30
- **Timezone:** Asia/Kolkata (IST, UTC+05:30)
- **Target duration:** originally ~5 hours (**estimate**); **re-baselined in
  correction M1 to ~8 hours** because the teacher-required deliverables
  (US-12 tests, US-13 CI/CD, US-14 Agile tracking incl. GitHub board,
  US-17 burndown) plus a functional audio path (US-03/US-04) honestly do not
  fit in 5 hours. The 5-hour figure is kept below as history; it is not
  the current plan.
- **Sprint goal:** A demonstrable Streamlit MVP where a student selects a
  Distributed Systems question, answers aloud (functional audio path) or
  typed (interim fallback), edits the transcript, sees covered/missed
  concepts with evidence, retries, and compares attempts — built with tests,
  CI, Kanban, backlog priorities, and an hourly burndown.
- **Capacity assumption:** 1 developer. Reviews are self-review + test run
  (no second person available tonight).

## Correction M1 (2026-10-09, ~00:25 IST) — what changed and why

Teacher requires Kanban, sprint backlog, story priorities, burndown chart,
and GitHub Actions CI/CD. The M0 plan left US-12/13/14 as stretch and had no
burndown story, and treated audio as an expendable spike. Corrected:

1. **US-12 (tests), US-13 (CI/CD), US-14 (Agile tracking) promoted P1 → P0.**
2. **US-17 (hourly burndown) added as P0** — no burndown story existed.
3. **US-03/US-04 audio promoted** from 30-min timeboxed spike to committed
   functional path (40 + 35 min). Typed-only is an interim prototype, not the
   completed spoken-viva experience.
4. **Reduced before cutting required work:** US-09 polish trimmed 40→30 min;
   US-15 interactive follow-ups and US-16 charts deferred post-MVP
   (follow-up content still ships inside US-10 data; US-07 comparison stays
   the committed progress view).
5. **US-11:** 20-min story, 5 min credited to M0 docs, 15 min remaining code work.
6. **Honest total: 485 min (~8.1 h).** Not forced to fit 5 hours.

## Committed scope — 485 min

| Story | Title | Est. | Tasks |
|-------|-------|------|-------|
| US-10 | Curated 15-Q bank (`data/questions.json` + loader + tests) | 60 min | Author 15 DS Qs; concepts/weights/phrases/negatives/reference/follow-up; loader + validation; pytest |
| US-06 | Rubric evaluation + evidence, negation-safe | 60 min | Deterministic matcher; weights math; evidence spans; negation guard; disclaimer; matcher tests |
| US-02 | Typed-answer mode | 25 min | Text input; route into review/edit → evaluate path |
| US-05 | Review/edit before evaluation | 20 min | Editable pre-eval text; empty-input rejection |
| US-01 | Question select | 20 min | List 15; select → prompt view; offline, no login |
| US-08 | SQLite history + progress | 35 min | Schema + insert/list; history + per-question progress |
| US-07 | Retry + compare | 30 min | Retry same rubric version; side-by-side delta |
| US-09 | Streamlit end-to-end flow (polish trimmed) | 30 min | Wire select→answer→review→evaluate→retry; 3.11 run command |
| US-11 | Guardrails in code (15 of 20; 5 in M0 docs) | 15 min | Audio non-retention path + limitation strings |
| US-03 | Record/upload audio (functional path) | 40 min | Record + upload with graceful degradation |
| US-04 | Transcription adapter (functional path) | 35 min | Interface + free default backend + typed-mode fallback |
| US-12 | Meaningful tests, CI-safe | 40 min | Matcher/schema/persistence tests; no network/models/creds |
| US-13 | GitHub Actions CI + versioned archive | 30 min | `ci.yml` + `release.yml`; archive ≠ hosting |
| US-14 | Agile tracking remainder (GitHub Issues + board) | 25 min | Required; blocker reported honestly if auth/API fails |
| US-17 | Hourly burndown | 20 min | `docs/burndown.md` + hourly events |

Deferred post-MVP: US-15 interactive flow, US-16 charts (both P2).

## Workload tradeoff (explicit — plan exceeds 5 h)

- The original 295-min/5-hour commitment is **superseded**. Current committed
  total is **485 min (~8.1 h)**; the sprint runs long rather than dropping
  teacher-required deliverables.
- Reductions were applied to polish/optionals first (US-09 −10, US-15/US-16
  deferred). Required deliverables (US-12/13/14/17, audio path) are cut last —
  effectively never: if time runs out, the vertical slice demos with typed
  mode while audio/CI finish, and the burndown shows it honestly.
- **Checkpoint rule (hourly):** at each hour mark per `docs/burndown.md`,
  compare actual vs. ideal remaining; if behind by >30 min, narrow (don't
  drop) the current story and defer its polish to the end of the queue.

## Definition of Done (applies to every committed story)

- [ ] Acceptance criteria in `docs/product_backlog.md` verified by hand or test.
- [ ] No secrets, no raw audio, no generated DB committed (`git status` clean of them).
- [ ] `docs/kanban.md` card moved with WIP rule respected (max 1 implementation
  story In Progress).
- [ ] `docs/progress_events.jsonl` appended (ISO timestamp + TZ, story ID,
  event type, remaining-minutes estimate).
- [ ] Sprint goal still demonstrable end-to-end after the change.

A story is NOT done if tests need network/model downloads/credentials, or if
the app claims coverage measures correctness/confidence/intelligence/speaking ability.

## Burndown

Tracked in `docs/burndown.md` (hourly: ideal vs. actual remaining minutes)
with inputs from `docs/progress_events.jsonl`. Scope changes are separate
events; initial estimates are never rewritten.
