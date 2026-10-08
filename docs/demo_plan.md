# VivaMirror — Demo Plan (Milestone 4: typed + spoken flow)

Total: ~5 minutes. One typed question, one spoken question. State the input
mode aloud every time it matters.

Launch: `.\.venv\Scripts\python.exe -m streamlit run app/main.py`
Audio install (once): `.\.venv\Scripts\python.exe -m pip install -r requirements-audio.txt`

## Setup (before audience)

- App running via the documented command; audio stack installed.
- CAP theorem question ready ("CAP theorem — advanced", ID ds-15).
- First transcription of the session may take ~15 s (one-time model
  download); transcribe the demo clip once beforehand so the cache is warm.
- Health evidence: `/_stcore/health` → `ok` (HTTP 200); AppTest suite
  (13 spoken-flow tests drive the real uploader + adapter with a labeled
  test double; 1 test forces the speech stack absent and runs typed only).

## Act 1 — Typed answer → missed concepts (1 min)

1. Keep **Typed answer** mode; show the mode label and the notice that
   nothing is saved.
2. Type a deliberately thin answer: `CAP is about databases. I think
   partitions matter somehow.` → Review → Evaluate.
3. Show: **Concept coverage: 0.0%**, four `not_detected` concepts with
   weights, the not-a-correctness-grade note. No reference visible yet.

## Act 2 — Spoken answer → transcript → review → coverage (2.5 min)

1. Switch to **Spoken answer** mode. State: "spoken mode — typed draft kept,
   previous result cleared."
2. **Upload** a short pre-recorded WAV (≤20 MB, ≤3 min; e.g. the rehearsed
   CAP answer). If the room PC allows mic use, record live instead — either
   way, play it back first so the audience hears the source audio.
3. Click **Transcribe** (explicit — nothing auto-transcribes). Point at the
   loading state, then the editable transcript in review.
4. Fix one word by hand to demonstrate that transcription accuracy and
   concept coverage are separate things, then **Evaluate**.
5. Show covered concepts with earned weights and quoted evidence, the
   "spoken answer (transcribed)" caption, then open the reference expander
   and read the assisted-practice note aloud.

Rehearsed upload script (reads at ~100.0% on ds-15): "Since network splits
will eventually happen, I must choose between consistency and availability;
the trade-off applies during a partition. My CP design will refuse
minority-side writes and reconcile divergent replicas afterwards, because
without partitions all three hold and the pick-two slogan is misleading."

## Act 3 — Failure honesty (0.5 min, live or narrated)

1. Upload a corrupt/oversized file (or narrate): the app rejects it before
   inference with a size/format message and offers typed practice.
2. If transcription ever fails live: read the error aloud, switch to Typed
   mode, continue. Never present a canned transcript as real speech.

## Not yet demoable (say so explicitly)

- **Retry comparison / history (US-07/US-08):** "Try again" restarts
  in-session only; nothing persists, no side-by-side view yet.
- **Mic widget in this room:** if the browser blocks the microphone, say so
  and use the upload path — same review → evaluate flow.

## Fallback lines (honesty script)

- "Coverage counts rubric concepts evidenced in the text — it is not a grade
  of correctness, confidence, intelligence, or speaking ability."
- "That attempt used typed mode." / "That attempt used transcribed speech —
  I corrected the transcript before evaluating."
- "Audio stays in this session only; nothing is saved or uploaded."

## Teacher-requirement evidence (30 s, after the app demo)

Show `docs/kanban.md`, `docs/sprint_backlog.md` priorities, the verified
GitHub Project board/issues, `docs/burndown.md` with the H1 checkpoint, and
note US-13 CI (`ci.yml` lint+test; `release.yml` versioned archive on tag;
archive ≠ hosting) as the next required deliverable. No speech-model
downloads or credentials in the default test suite.
