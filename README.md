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
- Spoken answers (optional): `.\.venv\Scripts\python.exe -m pip install -r requirements-audio.txt`
  (`faster-whisper==1.2.1`, `av==18.1.0`, CPU-only wheels). Typed practice
  launches and runs fully without it — see §11.
- The app opens in the browser automatically; stop it with `Ctrl+C`.
- No login, API keys, or model downloads anywhere except the documented
  first-run speech-model download (§11).

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

Included (status as of Milestone 4):

- Streamlit interface, Python 3.11. ✅ working (typed + spoken flow).
- Distributed Systems only, 15 curated questions + rubrics
  (concepts, weights, accepted phrases, reference answers, follow-ups). ✅
- Microphone recording / audio upload where the browser/OS supports it. ✅
  (upload verified by tests; mic widget rendered — browser check outstanding)
- Replaceable transcription adapter (default: free/local, no paid API). ✅
  (faster-whisper CPU/int8 base.en; real local check passed)
- Typed-answer mode, usable even when transcription is unavailable. ✅
  (verified with speech stack forcibly absent)
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
- **Session-only.** Nothing is saved unless you press **Save attempt**:
  saved attempts live in a local SQLite database (see §12). No history,
  no accounts, no audio retention at all beyond the session.
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
and `510d3c2` (feedback UI).

## 11. Spoken answers (US-03/US-04, Milestone 4)

- **Install:** core app needs only `requirements.txt`. For speech, add
  `.\.venv\Scripts\python.exe -m pip install -r requirements-audio.txt`.
  Without it, typed practice works fully; the spoken UI explains the missing
  dependency and every transcription failure routes back to typing.
- **Backend/model:** faster-whisper on CPU (`int8`), model `base.en`
  (~150 MB). The model object loads on first transcription only.
- **First run:** needs internet, ~150 MB disk, and patience (measured
  14.8 s first load including download on the dev machine; ~2.5 s inference
  for a 9 s clip). Afterwards the local Hugging Face cache makes it work
  offline. A failed download raises a clear error — transcription is never
  silently faked.
- **Microphone/browser:** the Record widget needs microphone permission and
  works on localhost/HTTPS. If the browser cannot record, use the upload
  alternative (same review → evaluate path).
- **Supported formats and limits:** wav, mp3, m4a, ogg/oga, flac, webm;
  max **20 MB** and **3 minutes**, checked before expensive inference.
  Corrupt/unsupported files are rejected safely with a helpful message.
- **Privacy/session behavior:** audio stays in the browser session for
  playback until replaced, the question changes, or the page closes. It is
  never uploaded anywhere and never saved by the app; transcription stages
  it through a short-lived temp file deleted immediately after (success and
  error paths). Raw audio is git-ignored and never committed.
- **What transcription is not:** the adapter returns transcript, language,
  duration, and backend/model metadata only — no confidence values, no
  speaking scores. Transcription accuracy and concept coverage are shown as
  separate things, and the transcript must be reviewed/edited before it can
  be evaluated.
- **Honest verification status:** real local transcription verified with a
  synthetic Windows-TTS WAV (exact transcript, `en`, 8.92 s duration).
  Microphone recording itself needs a browser with mic permission — a manual
  check still outstanding (see demo plan).

## 12. Attempt history, retry, and comparison (US-07/US-08, Milestone 5)

- **Database location and privacy:** saved attempts live in
  `data/local/vivamirror.db` (SQLite, git-ignored local runtime data; set
  `VIVAMIRROR_DB` to override the path). Everything stays on this computer —
  one shared installation history, no accounts, no user separation, no
  network. Each row holds: attempt ID, UTC timestamp, question ID, rubric
  snapshot + fingerprint, evaluator version, input mode, reviewed text,
  full result, coverage, and whether the reference was revealed.
  **Raw audio is never stored** (the schema has no audio column; saving
  audio is refused by validation and covered by tests).
- **Explicit saving and deletion:** nothing autosaves — press **Save attempt**
  after an evaluation. Re-clicking never duplicates (stable per-evaluation
  ID + database uniqueness). Delete one attempt any time; **Delete all**
  needs the explicit confirmation checkbox. History shows a helpful empty
  state when there is nothing saved.
- **Retry/comparison behavior:** Practice → Save → **Try again** (same
  question, fresh transient state, prior saves kept) → Save → History →
  pick two attempts → **Compare**. Deltas are reported in **percentage
  points**, with newly-covered and regressed concepts plus both reviewed
  answers for inspection.
- **Assistance and comparison limitations:** revealing the reference marks
  the question assisted for the session (Try again does not reset it);
  cross-session assistance cannot be established, and the UI says so. If
  rubric/evaluator versions differ, the direct delta is disabled with a
  warning instead of an invalid comparison — historical answers are never
  reinterpreted. Higher coverage never proves improved correctness or
  speaking ability.
