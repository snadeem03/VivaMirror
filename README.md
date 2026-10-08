# VivaMirror — A Practice Viva That Shows What You Missed

> **Milestone 3 status: typed-answer practice flow works.**
> Implemented so far: curated 15-question bank + validation (US-10), CAP
> rubric clarification, evidence-based evaluator (US-06), and the Streamlit
> typed flow — question select → type → review/edit → evaluate → feedback
> (US-01/US-02/US-05). Not yet built: audio/transcription (US-03/US-04),
> SQLite history and retry comparison (US-07/US-08), CI workflows (US-13).

## 0. Installation and launch (Windows PowerShell, Python 3.11)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests/ -q   # full suite, no network/models/credentials
.\.venv\Scripts\python.exe -m streamlit run app/main.py
```

- Runtime: `requirements.txt` (`streamlit==1.65.0`, tested — not a lockfile).
- Development (tests): `requirements-dev.txt` (adds `pytest==9.1.1`).
- The app opens in the browser automatically; stop it with `Ctrl+C`.
- Audio answers are **not available yet**: the UI is explicitly labeled
  "Typed practice mode". No login, API keys, or model downloads anywhere.

## 1. Problem

Viva / oral exams reward clear, complete spoken explanations, but students
usually prepare by silently re-reading notes. They discover gaps only during
the real viva — when it is too late. There is no tight loop for:
speak → see exactly which expected concepts were covered → see what was
missed → retry and compare.

## 2. Target users

- Primary: third-year IT undergraduates preparing for viva-voce exams
  (tonight's MVP: Distributed Systems only).
- Secondary: instructors / peers who want a transparent, rubric-based
  checklist of what a practice answer contained (with matched evidence),
  not a black-box score.

## 3. Proposed workflow (tonight's MVP)

1. Select a topic / question (1 of 15 curated Distributed Systems questions).
2. Answer by **typing** (audio recording/upload arrives in US-03/US-04;
   the UI says "typed practice" aloud and on screen).
3. (Later) Transcribe audio through a **replaceable transcription adapter**
   (no paid API by default).
4. **Review and edit** the typed answer before evaluation (two separate
   actions: "Review answer", then "Evaluate reviewed answer").
5. Evaluate against a **curated rubric**: required concepts, weights,
   accepted phrases, reference answer, follow-up questions.
6. See **covered / not detected / needs-review concepts** with matched
   evidence phrases and original-text offsets.
7. **Retry** the question in-session ("Try again"); persisted history and
   side-by-side comparison arrive with US-07/US-08.

## 4. MVP scope (tonight, ~5-hour accelerated student sprint)

Included (status as of Milestone 3):

- Streamlit interface, Python 3.11. ✅ working (typed flow).
- Distributed Systems only, 15 curated questions + rubrics
  (concepts, weights, accepted phrases, reference answers, follow-ups). ✅
- Microphone recording / audio upload where the browser/OS supports it. ⏳ US-03.
- Replaceable transcription adapter (default: free/local, no paid API). ⏳ US-04.
- Typed-answer mode, usable even when transcription is unavailable. ✅
- Editable transcript before evaluation. ✅ (review/edit screens, blank rejection)
- Transparent concept-coverage feedback with matched evidence spans. ✅
- Negation-safe matching: negated phrases (e.g. "not consistent",
  "never uses quorum") must NOT earn credit merely for containing a keyword. ✅
- SQLite attempt history + retry comparison. ⏳ US-07/US-08.
- No login, no model training, no arbitrary document ingestion. ✅

Explicitly out of scope for tonight:

- Other subjects, large question banks, document upload / RAG.
- Accounts, cloud sync, leaderboards.
- Paid transcription APIs as a requirement.
- Mobile app, hosting deployment.

## 5. Future scope (not tonight)

- More subjects and larger curated banks with rubric versioning.
- Optional pluggable transcribers (e.g. faster-whisper) behind the adapter.
- Exportable practice reports (PDF/CSV).
- Instructor rubric editor with validation.
- Hosted demo deployment (distinct from the versioned archive produced by CI).

## 6. Planned stack

| Layer        | Choice (planned)                                              |
|--------------|---------------------------------------------------------------|
| UI           | Streamlit                                                     |
| Language     | Python 3.11 (`py -3.11` on Windows)                           |
| Evaluation   | Deterministic, rubric-driven matcher (phrase + negation rules) |
| Transcription| Adapter interface; default free/local, optional plugins later |
| Persistence  | SQLite (standard library `sqlite3`), local file               |
| Tests        | `pytest`; CI-safe (no model downloads, no credentials)        |
| CI/CD        | GitHub Actions: lint+test on push/PR; versioned archive on tag|
| Agile        | `docs/` artifacts + GitHub Issues + GitHub Project board      |

No heavyweight speech packages are installed in Milestone 0.

## 7. Honest limitations

- **Concept coverage ≠ correctness.** A high coverage percentage means the
  answer mentioned the rubric's expected concepts (with evidence); it does
  NOT measure complete correctness, confidence, intelligence, or speaking
  ability. The UI says so on every result.
- **Rubric-bound.** Feedback quality is limited to 15 hand-curated rubrics;
  valid paraphrases outside the accepted-phrase lists are reported as
  not detected (tested behavior, not a bug being hidden). Full rules and
  limits: `docs/evaluation.md`.
- **Typed-only for now.** There is no microphone path yet, so nothing here
  assesses speaking. Audio/transcription is committed scope (US-03/US-04),
  not cut.
- **Session-only.** Nothing is saved: no history, no accounts, no audio
  retention at all. SQLite history arrives with US-08.
- **Tonight's build is a practice aid**, not an examiner or grading authority.

## 8. Repository layout

```text
VivaMirror/
├── README.md
├── requirements.txt          # runtime (streamlit)
├── requirements-dev.txt      # dev (adds pytest)
├── docs/
│   ├── product_backlog.md
│   ├── sprint_backlog.md
│   ├── kanban.md
│   ├── burndown.md
│   ├── progress_events.jsonl
│   ├── architecture.md
│   ├── evaluation.md
│   └── demo_plan.md
├── .github/workflows/      # planned in CI milestone (US-13, not yet implemented)
├── app/
│   ├── main.py             # Streamlit typed-practice flow (US-01/US-02/US-05)
│   ├── flow.py             # Streamlit-independent state machine
│   ├── questions.py        # bank loader + validation (US-10)
│   └── evaluation.py       # concept-coverage evaluator (US-06)
├── data/questions.json     # 15 curated Distributed Systems rubrics
├── tests/                  # pytest suite, credential-free
└── .gitignore
```

## 9. Agile tracking (teacher requirements)

- Kanban board: `docs/kanban.md` (local mirror) + GitHub Project board
  https://github.com/users/snadeem03/projects/2 (verified, 5 columns +
  Priority/Estimate/Sprint fields).
- Sprint backlog: `docs/sprint_backlog.md` (one accelerated student
  development sprint, re-baselined to ~8 h in correction M1).
- User-story priorities: `docs/product_backlog.md` (P0/P1/P2) and GitHub
  issue labels: https://github.com/snadeem03/VivaMirror/issues.
- Burndown: `docs/burndown.md`, inputs from `docs/progress_events.jsonl`
  (append-only; ISO timestamps with timezone + remaining-minutes estimates).
- CI/CD in GitHub Actions: US-13, implemented in the CI milestone
  (lint+test on push/PR; versioned archive on tag) — not yet built.

## 10. How to verify Milestone 3

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -q
.\.venv\Scripts\python.exe -m streamlit run app/main.py
git -C "D:\-_-\VivaMirror" status
git -C "D:\-_-\VivaMirror" log --oneline -8
```

Expected: full suite green, app serving the typed flow (health:
`/_stcore/health` → `ok`), clean tree, commits `eeaf712` (flow helper)
and slice-2 feedback commit below.
