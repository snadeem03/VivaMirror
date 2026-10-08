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
- **Notes:** Primary delivery risk (Windows browser permissions/devices).

## US-04 — Replaceable transcription adapter, free by default (P0, 35 min)

- **Story:** As a developer, I can swap transcription backends behind one
  interface so that the default path needs no paid API.
- **Acceptance criteria:**
  - [ ] Single adapter interface (e.g. `transcribe(audio_bytes) -> text`).
  - [ ] Default implementation needs no paid API key and no model download
    in CI/tests (stub or documented local path).
  - [ ] Transcription failure shows a clear error and routes user to typed mode.
- **Dependencies:** None (interface first).
- **Notes:** No heavyweight speech packages in Milestone 0; wired in later milestone.

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

## US-09 — Streamlit end-to-end practice flow (P0, 40 min)

- **Story:** As a student, I can walk select → answer → review/edit →
  evaluate → retry/compare in one Streamlit app without logging in.
- **Acceptance criteria:**
  - [ ] All steps reachable in order with no login.
  - [ ] App runs on Python 3.11 via a documented command.
  - [ ] Focused on viva practice; Agile tracking stays in repo artifacts, not the app.
- **Dependencies:** US-01…US-08.

## US-10 — Curated 15-question Distributed Systems rubric bank (P0, 60 min)

- **Story:** As a student, I get 15 Distributed Systems questions each with
  required concepts, weights, accepted phrases, reference answer, and
  follow-up questions so that feedback is syllabus-grounded.
- **Acceptance criteria:**
  - [ ] 15 entries, Distributed Systems only, stored as validated data
    (e.g. `data/rubrics/*.json` + schema check).
  - [ ] Every concept has: id, label, weight, accepted-phrases list.
  - [ ] Every question has: reference answer + at least 1 follow-up question.
  - [ ] Weights per question sum to a documented total (e.g. 100).
- **Dependencies:** None (content work; unblocks US-01, US-06).

## US-11 — Privacy and honesty guardrails (P0, 20 min)

- **Story:** As a user, I get honest, privacy-respecting behavior so that
  I am never misled about what the app measures or what it stores.
- **Acceptance criteria:**
  - [ ] Raw audio not retained by default (verified by code path + test).
  - [ ] UI + README limitation statements present (coverage ≠ correctness etc.).
  - [ ] No login, no tracking, no paid-API requirement by default.
- **Dependencies:** US-03, US-09.

## US-12 — Meaningful automated tests, CI-safe (P1, 40 min)

- **Story:** As a developer, I have pytest coverage for the rubric matcher
  and core flows so that regressions (esp. negation handling) are caught.
- **Acceptance criteria:**
  - [ ] Tests for: coverage math, evidence spans, negation cases, empty input,
    rubric schema validation, attempt persistence (temp DB).
  - [ ] `pytest` passes with no network, no model downloads, no credentials.
- **Dependencies:** US-06, US-08, US-10.

## US-13 — GitHub Actions CI + versioned delivery archive (P1, 30 min)

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
- **Notes:** Planned in M0; implemented in the later CI milestone.

## US-14 — Agile tracking artifacts for teacher requirements (P1, 25 min, M0-planned)

- **Story:** As a student, I maintain Kanban, sprint backlog with priorities,
  burndown inputs, and CI evidence so that course process requirements are met.
- **Acceptance criteria:**
  - [ ] `docs/kanban.md`, `docs/sprint_backlog.md`,
    `docs/progress_events.jsonl` present and consistent.
  - [ ] GitHub Issues mirror stories with priorities + acceptance criteria.
  - [ ] GitHub Project board has Backlog/Ready/In Progress/Review/Done
    (+ Priority/Estimate/Sprint fields where supported).
- **Dependencies:** None (process track; M0 planning portion completes tonight).

## US-15 — Follow-up question prompts (P2, 15 min)

- **Story:** As a student, I see follow-up questions after evaluation so that
  I can deepen a viva-style exchange.
- **Acceptance criteria:**
  - [ ] At least 1 follow-up per question shown post-evaluation.
  - [ ] Selecting a follow-up starts a new attempt linked to the parent question.
- **Dependencies:** US-06, US-10.

## US-16 — Progress charts polish (P2, 20 min)

- **Story:** As a student, I see a small per-question coverage trend so that
  improvement is visible at a glance.
- **Acceptance criteria:**
  - [ ] Trend uses only local SQLite data; works with 1+ attempts.
  - [ ] No new dependencies beyond the approved stack.
- **Dependencies:** US-08.

---

### Effort summary

| Priority | Stories | Minutes |
|----------|---------|---------|
| P0 (essential) | US-01…US-11 (11 stories) | 385 |
| P1 (important) | US-12…US-14 (3 stories) | 95 |
| P2 (optional) | US-15…US-16 (2 stories) | 35 |
| **Total backlog** | **16 stories** | **515 min (~8.6 h)** |

The full backlog intentionally exceeds one ~5-hour sitting; the sprint
selects a feasible subset (see `docs/sprint_backlog.md` for explicit
tradeoffs). Priority order: all P0 first, then P1, then P2.
