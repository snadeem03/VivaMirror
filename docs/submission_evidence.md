# VivaMirror — Submission Evidence (Sprint 1)

All URLs below were verified live on 2026-10-09 (~02:45 IST); nothing is
invented. No screenshots are claimed — none were captured (no browser was
available; UI behavior is evidenced by 36 AppTest tests driving real widgets).

## 1. Project goal and implemented workflow

Practice viva voce: select 1 of 15 curated Distributed Systems questions →
answer typed or spoken (mic record / upload, explicit transcribe) →
review/edit → evaluate against the curated rubric (covered / not detected /
needs review with evidence spans and weights) → explicitly save → retry →
compare two saved attempts (percentage-point delta, newly covered/regressed).
Local-only: SQLite history, no login, no audio retention, no paid services.

## 2. Kanban board

- Remote (verified, 5 columns Backlog/Ready/In Progress/Review/Done +
  Priority/Estimate/Sprint fields, 17 story issues with values):
  https://github.com/users/snadeem03/projects/2
- Local mirror: `docs/kanban.md` (consistent as of this commit).

## 3. Sprint backlog

- `docs/sprint_backlog.md`: Sprint 1, accelerated student development sprint,
  start 2026-10-09T00:14:05+05:30 (Asia/Kolkata), re-baselined 295 → 485 min.
- Hourly plan + re-baseline rationale: `docs/burndown.md`.

## 4. Prioritized user-story evidence

Backlog with P0/P1/P2, acceptance criteria, estimates, dependencies:
`docs/product_backlog.md`. GitHub mirror (priorities in titles + labels,
criteria in bodies; US-01…US-17 map to issues #1…#17):
https://github.com/snadeem03/VivaMirror/issues
Done P0s: US-01…US-11 (issues #1–#11 closed with evidence comments except
#12), US-13 (#13 closed), US-10 (#10 closed). Open: #12 (tests, subtask
comments), #14 (tracking, waiting on this evidence), deferred P2s #15/#16.
Status at submission time is in §9; final closures are recorded in
`docs/progress_events.jsonl`.

## 5. Burndown

- Chart: `docs/burndown.png` (event-based steps, no interpolation; labeled
  M0/revised ideal lines; scope-change annotations; actual timestamps).
- Data: `docs/burndown.csv` (24+ rows, regenerated from events).
- Generate: `.\.venv\Scripts\python.exe scripts/make_burndown.py`
  (report deps: `requirements-report.txt`, matplotlib 3.11.2).
- H0/H1/H2 checkpoints in `docs/burndown.md`; H2 recorded late at 02:42
  with an explicit note (the 02:14 instant was not observed, not invented).

## 6. CI runs (real results, including the failure)

- Failed (honest history — missing-PyAV WAV probing; fixed by stdlib wave
  probing + regression test):
  https://github.com/snadeem03/VivaMirror/actions/runs/37841180925
- Green, Windows + Linux (ruff + 158 offline tests + JUnit artifacts):
  https://github.com/snadeem03/VivaMirror/actions/runs/37841640889
- Green on the v0.1.0 tag (checks before packaging):
  https://github.com/snadeem03/VivaMirror/actions/runs/37841934249
- Green on the delivery commit (this submission's CI):
  https://github.com/snadeem03/VivaMirror/actions/runs/37845254954
- CI does not verify real microphone recording or real speech-model
  inference (stated in `ci.yml`); those are manual checks (§8).

## 7. Release / delivery (automated delivery, NOT hosting)

- Release (verified, asset `vivamirror-v0.1.0.zip`, 38 tracked files,
  contents validated — required files present, no DB/audio/secrets):
  https://github.com/snadeem03/VivaMirror/releases/tag/v0.1.0
- Delivery run (checks → validated package → artifact + release asset):
  https://github.com/snadeem03/VivaMirror/actions/runs/37841934233
- Released commit: `fbc22b4` (the CI-green commit the tag points at).
  Current head additionally carries workflow-cosmetic edits, the burndown
  chart, and this evidence file — disclosed, not implied identical.

## 8. Meaningful commits, tests, and speech evidence (separated)

- Scope/plan: `f7ec919` M0 plan, `764a04e` M1 correction (295→485 min).
- Product: `f34462f` bank, `a1a7b61` CAP fix, `1af2096` evaluator,
  `eeaf712` flow helper, `510d3c2` feedback UI, `ff2b7f8` adapter,
  `b56e125` spoken integration, `c8b4abd` storage, `25824b6` comparison.
- Process: `7b19e73` CI, `fbc22b4` WAV-probe fix, `548aacb` delivery.
- Tests: 159 collected/passing, per-file split test_audio_ui 13,
  test_evaluation 35, test_flow 23, test_history_ui 12, test_question_bank
  30, test_store 20, test_transcribe 15, test_ui 11
  (`python -m pytest tests/ -q`); lint `ruff check app tests scripts` clean.
  (The M6 reconciliation event recorded 158/14 before the WAV-probe
  regression test was added; this is the corrected final count.)
- Mocked speech tests (labeled `FakeTranscriber` doubles, offline,
  model-free): transcription path, invalidation, limits, cleanup.
- REAL inference (separate, never mocked): synthetic Windows-TTS WAV,
  faster-whisper CPU/int8 `base.en` — 14.8 s first load incl. ~150 MB
  download, 2.5 s inference, exact transcript, language `en`, 8.92 s
  duration through the production adapter.

## 9. Story status at submission

Done: US-01…US-11, US-13; US-12/US-14/US-17 close with this milestone
(events + board + issues updated; see `docs/progress_events.jsonl` and
`docs/kanban.md`). Deferred post-MVP: US-15, US-16 (P2). Remaining
estimated effort after this milestone: 0 of 485 committed minutes.

## 10. Remaining manual checks and limitations

- Microphone recording in a real browser (permission + end-to-end spoken
  attempt) — explicitly outstanding; upload path is tested.
- Paraphrase-blind matching, session-only assistance, single-installation
  history, no hosting — all disclosed in README §§7/11/12 and
  `docs/evaluation.md`; coverage is never correctness.
