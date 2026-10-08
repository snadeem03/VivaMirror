# VivaMirror — Demo Plan (Milestone 5: save → retry → compare)

Total: ~6 minutes. Typed + spoken practice, two saved attempts, one
comparison. State the input mode and the assisted state aloud every time
they matter.

Launch: `.\.venv\Scripts\python.exe -m streamlit run app/main.py`
Audio install (once): `.\.venv\Scripts\python.exe -m pip install -r requirements-audio.txt`

## Setup (before audience)

- App running; audio stack installed; model cache warm (transcribe once
  beforehand — first run downloads ~150 MB).
- CAP theorem question ready ("CAP theorem — advanced", ID ds-15).
- Fresh local history (delete any rehearsal attempts via History → Delete
  all, with the confirmation checkbox) so attempt 1 vs. 2 is unambiguous.
- Health evidence: `/_stcore/health` → `ok` (HTTP 200); full suite 158/158
  incl. 12 History AppTest tests on temp databases (real DB never touched).

## Act 1 — Spoken answer → save (2 min)

1. Select the CAP question, switch to **Spoken answer** mode. State: "spoken
   mode — previous result cleared, typed draft kept."
2. **Upload** the rehearsed thin clip: "Network splits will eventually
   happen." (Or record it live if the mic works — either way, play it back
   first.) Click **Transcribe**, correct nothing (it is clean), Evaluate.
3. Show: **Concept coverage: 30.0%**, one covered concept with evidence.
4. Click **Save attempt** → "Saved attempt … stored locally on this computer
   only." State: "explicit save — nothing autosaves."

## Act 2 — Retry → improved answer → save (1.5 min)

1. Click **Try again** (same question; prior save kept; nothing persisted
   beyond the two saves you make).
2. Upload/record the improved script: "Since network splits will eventually
   happen, I must choose between consistency and availability; the
   trade-off applies during a partition. My CP design will refuse
   minority-side writes and reconcile divergent replicas afterwards,
   because without partitions all three hold and the pick-two slogan is
   misleading." → Review → Evaluate → **100.0%** → **Save attempt**.
3. Open **History** (sidebar): 2 saved attempts, best 100.0%, latest 100.0%,
   both labeled typed/spoken + assisted/unassisted honestly.

## Act 3 — Comparison (1.5 min)

1. In History, keep the two attempts selected, click **Compare**.
2. Show: earlier/later timestamps, 30.0% → 100.0%, **+70.0 percentage
   points** (say "percentage points, not percent"), newly-covered concepts
   (C/A trade-off, CP vs AP, no-forced-choice), both reviewed answers as
   plain text, and the warning that higher coverage does not prove improved
   correctness or speaking ability.
3. Mention: version mismatch would disable the delta with a warning instead
   of an invalid comparison; historical answers are never reinterpreted.

## Act 4 — Assistance + deletion honesty (0.5 min)

1. Back in Practice, click **Reveal reference answer** → reference appears
   with the assisted-practice note. State: "further practice is assisted
   this session; Try again does not reset it; a fresh session cannot prove
   assistance either way."
2. In History, delete one attempt, then (only if the room agrees) show the
   Delete-all confirmation checkbox. State: "saved answers remain locally
   on this computer; raw audio is never stored anywhere."

## Not yet demoable (say so explicitly)

- **Hosted deployment / CI evidence (US-13):** next required deliverable;
  the archive-vs-hosting distinction stands.
- **Mic widget in this room:** if the browser blocks the microphone, say so
  and use the upload path — same review → evaluate → save flow.

## Fallback lines (honesty script)

- "Coverage counts rubric concepts evidenced in the text — it is not a grade
  of correctness, confidence, intelligence, or speaking ability."
- "That attempt used transcribed speech — I corrected the transcript before
  evaluating." / "That attempt used typed mode."
- "Saved locally on this computer; audio is never stored."

## Teacher-requirement evidence (30 s, after the app demo)

Show `docs/kanban.md`, `docs/sprint_backlog.md` priorities, the verified
GitHub Project board/issues, `docs/burndown.md` checkpoints, and note US-13
CI as the remaining required build step. Default test suite has no
speech-model downloads or credentials.
