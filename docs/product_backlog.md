# VivaMirror — Product Backlog

Priorities: **P0 = essential** (tonight's MVP), **P1 = important**
(needed for a credible, demonstrable submission), **P2 = optional**
(only if time remains). Effort in **minutes** (single-student estimate).

> Source of truth for story list. Status lives in `docs/kanban.md`;
> time tracking lives in `docs/progress_events.jsonl`.

## US-01 — Browse and select a curated question (P0, 20 min)

- **Story:** As a student, I can list and select one of 15 curated
  Distributed Systems questions so that I practice a known syllabus item.
- **Acceptance criteria:**
  - [ ] Exactly the 15 curated questions are listed (Distributed Systems only).
  - [ ] Selecting a question shows its prompt and reference context.
  - [ ] Works without microphone, network, or credentials.
- **Dependencies:** US-10 (rubric/question dataset).
- **Notes:** No arbitrary document ingestion; fixed bank only.

## US-02 — Typed-answer mode independent of transcription (P0, 25 min)

- **Story:** As a student, I can type my answer directly so that I can
  practice even when microphone/transcription is unavailable.
- **Acceptance criteria:**
  - [ ] Text area available on the answer step without touching audio APIs.
  - [ ] Typed text flows into the same review/edit → evaluate path as transcripts.
  - [ ] Demo can state explicitly when typed mode was used.
- **Dependencies:** US-05, US-06.
- **Notes:** This is the fallback that keeps the core usable (delivery-risk hedge).

## US-03 — Record or upload an audio answer where supported (P0, 40 min)

- **Story:** As a student, I can record via microphone or upload an audio
  file where the browser/OS supports it so that I practice speaking aloud.
- **Acceptance criteria:**
  - [ ] Record and upload options are present but gracefully degrade
    with a clear message when unsupported.
  - [ ] Raw audio is NOT retained by default (in-memory/transient only;
    explicit opt-in required for any retention).
  - [ ] Typed mode (US-02) remains available regardless.
- **Dependencies:** US-04.
- **Notes:** A basic functional audio/transcription path is a committed
  product goal — the spoken viva is the point of the app. Typed-only is an
  interim prototype that keeps the loop usable, not the completed experience.
  (Correction M1: promoted from 30-min spike to full 40-min story.)

## US-04 — Replaceable transcription adapter, free by default (P0, 35 min)

- **Story:** As a developer, I can swap transcription backends behind one
  interface so that the default path needs no paid API.
- **Acceptance criteria:**
  - [ ] Single adapter interface (e.g. `transcribe(audio_bytes) -> text`).
  - [ ] Default implementation needs no paid API key and no model download
    in CI/tests (stub or documented local path).
  - [ ] Transcription failure shows a clear error and routes user to typed mode.
- **Dependencies:** None (interface first).
- **Notes:** Committed functional path (with US-03): a working adapter with a
  free default backend plus graceful degradation. No heavyweight speech
  packages in Milestone 0/1; backend wired in its own milestone.
  (Correction M1: promoted from spike timebox to full 35-min story.)

## US-05 — Review and edit transcript before evaluation (P0, 20 min)

- **Story:** As a student, I can review and edit the transcript/typed text
  before evaluation so that transcription errors don't silently distort feedback.
- **Acceptance criteria:**
  - [ ] Editable text shown pre-evaluation; edits are what gets evaluated.
  - [ ] Empty submission is rejected with a clear message.
- **Dependencies:** US-02, US-04.

## US-06 — Rubric evaluation with covered/missed concepts + evidence (P0, 60 min)

- **Story:** As a student, I can evaluate my (edited) answer against the
  curated rubric so that I see exactly which concepts were covered and which
  were missed, with evidence.
- **Acceptance criteria:**
  - [ ] Per-concept verdict (covered/missed) with weight shown.
  - [ ] Each "covered" verdict cites the matched evidence span from the answer.
  - [ ] Coverage % = sum(weights covered) / sum(weights); rubric shows weights.
  - [ ] **Negation-safe:** a negated phrase (e.g. "not consistent",
    "never uses quorum", "no leader election") does NOT earn credit merely
    for containing a keyword — covered by a dedicated test.
  - [ ] UI disclaimer: coverage measures rubric-phrase presence, NOT complete
    correctness, confidence, intelligence, or speaking ability.
- **Dependencies:** US-10.
- **Notes:** Deterministic matcher; no model training.

## US-07 — Retry a question and compare attempts (P0, 30 min)

- **Story:** As a student, I can retry a question and compare two attempts
  side by side so that I can demonstrate improvement.
- **Acceptance criteria:**
  - [ ] "Retry" reuses the same question/rubric version.
  - [ ] Comparison shows coverage %, covered/missed delta per concept.
  - [ ] Demo script (incomplete → missed; improved → higher coverage) is reproducible.
- **Dependencies:** US-06, US-08.

## US-08 — SQLite attempt history and progress view (P0, 35 min)

- **Story:** As a student, I can see my past attempts and progress per
  question so that practice accumulates across retries.
- **Acceptance criteria:**
  - [ ] Attempts persisted in local SQLite (question id, rubric version,
    transcript/edited text, per-concept results, coverage %, timestamp, input mode).
  - [ ] History list + per-question progress (attempt count, best/latest coverage).
  - [ ] DB file is git-ignored local runtime data; schema documented.
- **Dependencies:** US-06.

## US-09 — Streamlit end-to-end practice flow (P0, 30 min)

- **Story:** As a student, I can walk select → answer → review/edit →
  evaluate → retry/compare in one Streamlit app without logging in.
- **Acceptance criteria:**
  - [ ] All steps reachable in order with no login.
  - [ ] App runs on Python 3.11 via a documented command.
  - [ ] Focused on viva practice; Agile tracking stays in repo artifacts, not the app.
- **Dependencies:** US-01…US-08.
- **Notes:** Polish trimmed (correction M1): functional flow first; visual
  refinement deferred so required Agile/CI deliverables stay committed.

## US-10 — Curated 15-question Distributed Systems rubric bank (P0, 60 min)

- **Story:** As a student, I get 15 Distributed Systems questions each with
  required concepts, weights, accepted phrases, reference answer, and
  follow-up questions so that feedback is syllabus-grounded.
- **Acceptance criteria:**
  - [ ] 15 entries, Distributed Systems only, stored as validated data
    (`data/questions.json` + loader/validation module + pytest suite).
  - [ ] Every question has: stable unique ID, subject, topic, difficulty,
    question text, concise reference answer, 3–5 concepts, one follow-up.
  - [ ] Every concept has: ID, label, positive weight, explanation,
    accepted-phrases list (meaningful phrases, not loose single words),
    and relevant negative examples.
  - [ ] Weights per question sum to 100.
  - [ ] Loader works independent of CWD and imports neither Streamlit nor
    any speech model.
- **Dependencies:** None (content work; unblocks US-01, US-06).
- **Notes:** Phrase matching is presented as rubric evidence, never as proof
  of correctness. Negative examples support future evaluator tests; this
  milestone does not claim a complete negation detector.

## US-11 — Privacy and honesty guardrails (P0, 20 min)

- **Story:** As a user, I get honest, privacy-respecting behavior so that
  I am never misled about what the app measures or what it stores.
- **Acceptance criteria:**
  - [ ] Raw audio not retained by default (verified by code path + test).
  - [ ] UI + README limitation statements present (coverage ≠ correctness etc.).
  - [ ] No login, no tracking, no paid-API requirement by default.
- **Dependencies:** US-03, US-09.

## US-12 — Meaningful automated tests, CI-safe (P0, 40 min)

- **Story:** As a developer, I have pytest coverage for the rubric matcher
  and core flows so that regressions (esp. negation handling) are caught.
- **Acceptance criteria:**
  - [ ] Tests for: coverage math, evidence spans, negation cases, empty input,
    rubric schema validation, attempt persistence (temp DB).
  - [ ] `pytest` passes with no network, no model downloads, no credentials.
- **Dependencies:** US-06, US-08, US-10.
- **Notes:** Teacher-required (CI/CD). Promoted P1 → P0 in correction M1;
  committed scope, not stretch.

- **Story:** As a developer, I have pytest coverage for the rubric matcher
  and core flows so that regressions (esp. negation handling) are caught.
- **Acceptance criteria:**
  - [ ] Tests for: coverage math, evidence spans, negation cases, empty input,
    rubric schema validation, attempt persistence (temp DB).
  - [ ] `pytest` passes with no network, no model downloads, no credentials.
- **Dependencies:** US-06, US-08, US-10.

## US-13 — GitHub Actions CI + versioned delivery archive (P0, 30 min)

- **Story:** As a developer, pushes/PRs run lint+tests and version tags
  produce a downloadable app archive so that submission and delivery are repeatable.
- **Acceptance criteria:**
  - [ ] `ci.yml`: runs on push + PR; Python 3.11; lint + `pytest`;
    no speech-model downloads, no secrets required.
  - [ ] `release.yml`: on `v*` tag, runs checks then uploads a versioned
    archive (e.g. `vivamirror-<tag>.zip`) as a release asset.
  - [ ] Docs clearly distinguish **artifact delivery** (archive) from
    **hosting deployment** (not provided).
- **Dependencies:** US-12.
- **Notes:** Teacher-required (CI/CD). Promoted P1 → P0 in correction M1;
  implemented in this sprint, not a later milestone.

## US-14 — Agile tracking artifacts for teacher requirements (P0, 25 min, M0-planned)

- **Story:** As a student, I maintain Kanban, sprint backlog with priorities,
  burndown inputs, and CI evidence so that course process requirements are met.
- **Acceptance criteria:**
  - [ ] `docs/kanban.md`, `docs/sprint_backlog.md`,
    `docs/progress_events.jsonl` present and consistent.
  - [ ] GitHub Issues mirror stories with priorities + acceptance criteria.
  - [ ] GitHub Project board has Backlog/Ready/In Progress/Review/Done
    (+ Priority/Estimate/Sprint fields where supported).
- **Dependencies:** None (process track; M0 planning portion completes tonight).
- **Notes:** Teacher-required (Kanban). Promoted P1 → P0 in correction M1.
  GitHub board/Issues creation is required, not optional; if authentication
  or Project permissions fail it is reported as a blocker with exact setup
  commands — never silently dropped. Local artifacts remain the source of
  truth until the remote board is verified.

## US-15 — Follow-up question prompts (P2, deferred post-MVP)

- **Story:** As a student, I see follow-up questions after evaluation so that
  I can deepen a viva-style exchange.
- **Acceptance criteria:**
  - [ ] At least 1 follow-up per question shown post-evaluation.
  - [ ] Selecting a follow-up starts a new attempt linked to the parent question.
- **Dependencies:** US-06, US-10.
- **Notes:** Correction M1: interactive follow-up flow deferred post-MVP so
  teacher-required deliverables stay committed. The curated follow-up content
  itself still ships inside US-10 data.

## US-16 — Progress charts polish (P2, deferred post-MVP)

- **Story:** As a student, I see a small per-question coverage trend so that
  improvement is visible at a glance.
- **Acceptance criteria:**
  - [ ] Trend uses only local SQLite data; works with 1+ attempts.
  - [ ] No new dependencies beyond the approved stack.
- **Dependencies:** US-08.
- **Notes:** Correction M1: deferred post-MVP; first to cut so required
  Agile/CI deliverables stay committed. Retry comparison (US-07) remains the
  committed progress view.

## US-17 — Hourly burndown chart for the accelerated sprint (P0, 20 min)

- **Story:** As a student, I maintain an hourly burndown of actual remaining
  estimated effort versus ideal remaining effort so that sprint progress and
  scope changes are visible to my teacher.
- **Acceptance criteria:**
  - [ ] `docs/burndown.md` records hourly checkpoints (clock time + IST):
    ideal remaining vs. actual remaining estimated minutes.
  - [ ] Every scope change is recorded explicitly as a new
    `progress_events.jsonl` event; initial estimates are never rewritten.
  - [ ] Chart/table is derivable from `progress_events.jsonl` alone.
- **Dependencies:** US-14.
- **Notes:** Added in correction M1 — no burndown story existed; the teacher
  explicitly requires a burndown chart.

---

### Effort summary (revised in correction M1 — honest total, not fitted to 5 h)

| Priority | Stories | Minutes |
|----------|---------|---------|
| P0 (essential + teacher-required) | US-01…US-14 + US-17 (15 stories) | 485 |
| P2 (deferred post-MVP) | US-15, US-16 | 0 in sprint |
| **Committed sprint total** | **15 stories** | **485 min (~8.1 h)** |

Breakdown: US-01 20 + US-02 25 + US-03 40 + US-04 35 + US-05 20 + US-06 60
+ US-07 30 + US-08 35 + US-09 30 + US-10 60 + US-11 15 + US-12 40 + US-13 30
+ US-14 25 + US-17 20 = **485 min**.

The committed total exceeds the original ~5-hour estimate. This is stated
plainly: the teacher-required deliverables (tests, CI/CD, Agile tracking,
burndown) plus a functional audio path do not fit in 5 hours alongside the
full practice loop. Reductions applied first (US-09 polish 40→30, US-15/US-16
deferred); required deliverables are never the first cut. See
`docs/sprint_backlog.md` for the revised plan and `docs/burndown.md` for
hourly tracking against a re-baselined ideal line.
