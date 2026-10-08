# VivaMirror — CONTEXT (resume-from-here handoff)

> Read this file first in any new session. It summarizes everything built
> through Milestone 6 (2026-10-09 ~03:25 IST) so work can continue without
> re-discovering the repo. Verify claims against the repo before acting on
> them; do not assume this file is newer than the working tree
> (`git status`, `git log --oneline -5`).

## 1. What this is

**VivaMirror — A Practice Viva That Shows What You Missed.** A Streamlit
app (Python 3.11, Windows PowerShell dev machine) where a third-year IT
student picks 1 of 15 curated Distributed Systems viva questions, answers
typed or spoken (mic record / upload → local faster-whisper transcription),
reviews/edits the text, gets evidence-based concept coverage
(covered / not_detected / needs_review with weights + original-text
offsets), explicitly saves attempts to local SQLite, retries, and compares
two attempts (percentage-point delta). No login, no audio retention, no
paid APIs, no hosting.

## 2. Environment (verified)

- Repo: `D:\-_-\VivaMirror`, branch `main`, remote
  `https://github.com/snadeem03/VivaMirror.git` (public, pre-existing empty
  repo reused — never create duplicates).
- GitHub: user `snadeem03`, `gh` authenticated; project board
  https://github.com/users/snadeem03/projects/2 (columns
  Backlog/Ready/In Progress/Review/Done + Priority/Estimate/Sprint fields);
  issues #1…#17 map to US-01…US-17 (all P0s closed with evidence comments).
- venv `.venv/` = **Python 3.11.9** (system default `python` is 3.14 — always
  use `.\.venv\Scripts\python.exe`). Tested versions: streamlit 1.65.0,
  pytest 9.1.1, ruff 0.16.10, faster-whisper 1.2.1, av 18.1.0,
  matplotlib 3.11.2.
- Dependency split: `requirements.txt` (runtime: streamlit),
  `requirements-dev.txt` (adds pytest, ruff), `requirements-audio.txt`
  (faster-whisper, av — optional), `requirements-report.txt` (matplotlib).
- No `AGENTS.md` exists. Global git config untouched (user snadeem03).
- Sprint: Sprint 1, accelerated student sprint, start
  2026-10-09T00:14:05+05:30 (Asia/Kolkata). Scope re-baselined M0 295 min →
  M1 **485 min**; **0 of 485 committed minutes remain** (all P0s Done;
  P2s US-15/US-16 deferred post-MVP).

## 3. Repo layout (all implemented)

```text
app/main.py          # Streamlit entry (Practice/History nav, typed+spoken)
app/flow.py          # Streamlit-independent state machine (stages, save IDs)
app/questions.py     # bank loader + validation (stdlib only)
app/evaluation.py    # concept-coverage matcher (EVALUATOR_VERSION = "1")
app/transcribe.py    # faster-whisper CPU/int8 base.en adapter (lazy imports)
app/store.py         # SQLite history (SCHEMA_VERSION = 1, temp-DB tested)
data/questions.json  # 15 DS rubrics (weights sum to 100; ds-15 CAP clarified)
scripts/make_burndown.py  # events → docs/burndown.csv + docs/burndown.png
tests/               # 159 tests: audio_ui 13, evaluation 35, flow 23,
                     # history_ui 12, question_bank 30, store 20,
                     # transcribe 15, ui 11
docs/                # product_backlog, sprint_backlog, kanban, burndown.md,
                     # progress_events.jsonl (source of truth for tracking),
                     # architecture, evaluation, demo_plan, submission_evidence
.github/workflows/  # ci.yml (push+PR, py3.11, win+ubuntu, ruff+pytest,
                     # JUnit artifacts) + release.yml (v* tags → validated ZIP)
data/local/vivamirror.db  # local runtime DB (git-ignored; VIVAMIRROR_DB overrides)
```

Key commands (repo root, PowerShell):

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -q
.\.venv\Scripts\python.exe -m ruff check app tests scripts
.\.venv\Scripts\python.exe -m streamlit run app/main.py
.\.venv\Scripts\python.exe scripts/make_burndown.py
```

## 4. Milestone history (commit hashes)

- M0 `f7ec919` plan/scope · M1 `764a04e` correction (485 min) + `f34462f`
  question bank · M2 `a1a7b61` CAP fix + `1af2096` evaluator ·
  M3 `eeaf712` flow helper + `510d3c2` feedback UI · M4 `ff2b7f8` adapter
  + `b56e125` spoken integration · M5 `c8b4abd` storage + `25824b6`
  comparison · M6 `7b19e73` CI + `fbc22b4` WAV-probe fix + `548aacb`
  delivery/chart + `488a2c7` evidence (HEAD, pushed, CI green).
- Tag **`v0.1.0`** → commit `fbc22b4`; release
  https://github.com/snadeem03/VivaMirror/releases/tag/v0.1.0
  (`vivamirror-v0.1.0.zip`, 38 files, validated). Later commits are
  workflow-cosmetic + chart + evidence only (disclosed in README §0b).
- CI runs: failure `37841180925` (honest history, fixed) → green
  `37841640889` (win+linux), `37841934249` (tag), `37845254954`,
  `37845840160`. Release run `37841934233` green.
- Real speech check (not mocked): synthetic Windows-TTS WAV →
  base.en exact transcript, `en`, 8.92 s (14.8 s first load incl. download,
  2.5 s inference). Mocked path uses labeled `FakeTranscriber` doubles only.

## 5. Conventions that must be kept

- **Tracking:** `docs/progress_events.jsonl` is append-only (ISO+TZ
  timestamps, story ID, event, remaining-minutes estimate). Never rewrite
  history — append correction events. `docs/kanban.md` mirrors board state;
  WIP = max 1 implementation story In Progress. Burndown inputs only from
  real events; H3 (03:14) and later checkpoints do not exist yet.
- **Stories:** close GitHub issues only with evidence comments; update
  Project Status fields to match (option IDs documented in session history;
  re-query via GraphQL if unsure). Keep US-12-style stories open until all
  subtasks land.
- **Tests:** temp DBs/files only, never the real bank/DB; fictional answers
  only; AppTest drives real widgets (`file_uploader.set_value((name, bytes,
  mime))`); `st.audio_input` has NO AppTest accessor (browser-only);
  test seams allowed only if documented (`vm_transcriber`,
  `VIVAMIRROR_DB` env). No speech-model downloads or credentials in the
  default suite.
- **Code rules:** stdlib-only core (`questions`, `evaluation`, `store`,
  `flow`); lazy speech imports; student text rendered via `st.text` only
  (never markdown/HTML); parameterized SQL; temp files deleted in
  `finally`; answer text only sliced, never executed.
- **Git:** meaningful separate commits, explicit `git add` file lists,
  review diff first; push normally and verify (`git status`, log hashes,
  `gh run list`); NEVER force-push, amend pushed commits, or move tags.
- **Docs:** README §§0/0b/7/11/12 hold install/launch/limits/privacy/release
  truth; `docs/demo_plan.md` is the live demo script; `docs/evaluation.md`
  documents matcher limits; `docs/submission_evidence.md` holds verified URLs.

## 6. What's left / known gaps

- Deferred P2s: US-15 interactive follow-ups, US-16 progress charts.
- Manual checks outstanding: **mic recording in a real browser**
  (permission + end-to-end spoken attempt); >3-min real clip for duration
  limits; first-run model download on a fresh machine.
- H3+ burndown checkpoints only if sprint work resumes (none exists now).
- Known product limits: paraphrase-blind matching, session-only assistance,
  single-installation history, no hosting (all disclosed in README/docs).
- A future v0.1.1+ tag must NOT move v0.1.0; follow the same sequence:
  green CI → tag → verify release workflow → record evidence.

## 7. Suggested next actions (pick one)

1. Manual browser pass (mic record → transcribe → save → compare), then log
   results as a progress event.
2. A P2 (US-15/US-16) as a new milestone with its own branch of events.
3. H3 checkpoint + chart regen if/when new work lands.
