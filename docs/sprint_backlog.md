# VivaMirror — Sprint Backlog

## Sprint label (explicit)

> **Sprint 1 — Accelerated student development sprint (tonight's MVP build).**
> This is the ONLY sprint in tonight's plan. The 30–60-minute implementation
> work packages listed in the final report are **milestones within this single
> sprint**, not separate Scrum sprints.

- **Sprint start (actual):** 2026-10-09T00:14:05+05:30
- **Timezone:** Asia/Kolkata (IST, UTC+05:30)
- **Target duration:** ~5 hours (**estimate, not a guarantee** — single-student,
  evening build; interruptions and Windows audio troubleshooting may shift it).
- **Sprint goal:** A demonstrable Streamlit MVP where a student selects a
  Distributed Systems question, answers (typed mode guaranteed; audio
  best-effort), edits the transcript, sees covered/missed concepts with
  evidence, retries, and compares attempts — with attempts in local SQLite.
- **Capacity assumption:** 1 developer, ~300 focused minutes. Reviews are
  self-review + test run (no second person available tonight).

## Selected stories (committed vs. stretch)

Full backlog = 515 min (~8.6 h) — deliberately larger than one sitting.
Committed scope below is trimmed to fit ~5 h; everything else is stretch
(see tradeoffs).

### Committed (must finish for a demonstrable MVP) — 295 min

| Story | Title | Estimate | Tasks |
|-------|-------|----------|-------|
| US-10 | Curated 15-Q rubric bank | 60 min | Draft 15 DS questions; per-concept weights/phrases/reference/follow-ups; JSON schema + validation script |
| US-06 | Rubric evaluation + evidence, negation-safe | 60 min | Deterministic matcher; weights math; evidence spans; negation guard; disclaimer text; unit tests for matcher |
| US-02 | Typed-answer mode | 25 min | Answer-step text input; route into review/edit → evaluate path |
| US-05 | Review/edit before evaluation | 20 min | Editable pre-eval text; empty-input rejection |
| US-01 | Question select | 20 min | List 15; select → prompt view; no-login, offline |
| US-08 | SQLite history + progress | 35 min | Schema + insert/list; history + per-question progress view |
| US-07 | Retry + compare | 30 min | Retry same rubric version; side-by-side delta (coverage %, concept deltas) |
| US-09 | Streamlit end-to-end flow | 40 min | Wire select→answer→review→evaluate→retry; `py -3.11 -m streamlit run` documented |
| US-11 (incremental) | Privacy/honesty guardrails in code | 5 min | Audio non-retention code path + limitation strings (bulk of US-11 already done in M0 docs) |

Committed total: **295 min ≈ 4.9 h** — fits the ~5 h estimate.

### Stretch (only if committed scope is green) — in priority order

| Story | Title | Estimate | Note |
|-------|-------|----------|------|
| US-03/04 (spike) | Audio record/upload + adapter stub | 30 min timebox | Graceful-degrade UI + stub adapter; full device testing deferred — typed mode guarantees the demo |
| US-12 | Meaningful tests, CI-safe | 40 min | Matcher + schema + persistence tests (`pytest`, no network/models/creds); partly overlaps US-06/US-08 work above |
| US-14 (remainder) | GitHub Issues + Project board | 25 min | Blocked on `gh` auth (see §7); local artifacts already done in M0 |
| US-13 | CI + versioned archive workflows | 30 min | `ci.yml` + `release.yml`; planned now, implemented in CI milestone |
| US-15 | Follow-up prompts | 15 min | Show post-eval follow-ups |
| US-16 | Progress charts polish | 20 min | Coverage trend from SQLite |

Stretch total: 160 min. Committed + stretch = 455 min (~7.6 h).

## Workload tradeoff (explicit — plan exceeds 5 h if stretch is included)

1. The **committed 295 min** is the tonight-MVP promise; stretch is explicitly
   **not promised** for the ~5 h window.
2. **Audio (US-03/US-04) is a 30-minute timeboxed spike, not a committed
   deliverable.** Rationale: Windows browser mic permissions are the top
   delivery risk; typed mode (US-02) guarantees the evaluative loop works.
   If audio works, keep it; if not, demo real-transcription readiness via the
   adapter stub + typed mode, and say so explicitly (see `demo_plan.md`).
3. **US-12 testing is folded into matcher/persistence work** where possible
   (write tests alongside US-06/US-08) rather than as a separate 40-min block.
4. **US-13 release workflow and US-15/US-16 are first to cut** if the 3-hour
   checkpoint shows slippage. Cut order: US-16 → US-15 → US-13 (keep `ci.yml`
   plan documented) → narrow US-12 to negation + math tests only.
5. **3-hour checkpoint rule:** at ~180 min elapsed, compare done vs. committed;
   if behind by >30 min, drop remaining stretch and timebox audio to zero
   (typed-only demo).

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

## Burndown input

Remaining-minutes estimates are recorded per event in
`docs/progress_events.jsonl` (M0 records initial estimates + planning
completion only — no invented implementation progress). The burndown itself is
derived from that file during the sprint.
