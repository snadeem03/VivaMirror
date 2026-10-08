# VivaMirror — Demo Plan (Milestone 3: working typed flow)

Total: ~4 minutes. One question, two in-session attempts. State aloud that
this is **typed practice** — audio is not built yet.

Launch: `.\.venv\Scripts\python.exe -m streamlit run app/main.py`

## Setup (before audience)

- App running via the documented command above.
- CAP theorem question selected ("CAP theorem — advanced", ID ds-15).
- Health evidence on hand: `/_stcore/health` → `ok` (HTTP 200), plus the
  AppTest suite (11 UI tests drive the real widgets).

## Act 1 — One incomplete answer → missed concepts (1.5 min)

1. Show the question selector (15 curated, Distributed Systems only) and the
   "Typed practice mode" notice.
2. Type a deliberately thin answer: `CAP is about databases. I think
   partitions matter somehow.`
3. Click **Review answer** — point out the editable review screen, keep text
   as-is, click **Evaluate reviewed answer**.
4. Show: **Concept coverage: 0.0%**, four `not_detected` concepts with
   weights, the "not a correctness grade" explanation, and that no reference
   answer is visible yet.

Expected: 0.0%, explicit missed list, no reference shown.

## Act 2 — One improved answer → increased coverage (1.5 min)

1. Click **Try again** (same question, fresh in-session attempt — no history
   is stored anywhere).
2. Type: `Since network splits will eventually happen, I must choose
   between consistency and availability; the trade-off applies during a
   partition. My CP design will refuse minority-side writes and reconcile
   divergent replicas afterwards, because without partitions all three hold
   and the pick-two slogan is misleading.`
3. Review → Evaluate. Show: **Concept coverage: 100.0%**, covered concepts
   with earned weights and quoted evidence, then open the reference-answer
   expander and read the assisted-practice note aloud.

Expected: 100.0% with evidence spans; reference visible only post-evaluation.

## Act 3 — Blank rejection + edit invalidation (0.5 min, live)

1. Try again, click **Review answer** with an empty box → helpful
   blank-submission warning, no evaluation.
2. After an evaluation, click **Edit answer** → result disappears and the
   reference expander hides; the previous result never leaks.

## Not yet demoable (say so explicitly)

- **Retry comparison / history (US-07/US-08):** "Try again" restarts
  in-session only; nothing is persisted, no side-by-side view exists yet.
- **Audio transcription (US-03/US-04):** typed mode shown instead; never fake
  a transcription. The honesty line: "That attempt used typed mode."

## Fallback lines (honesty script)

- "Coverage counts rubric concepts evidenced in the text — it is not a grade
  of correctness, confidence, intelligence, or speaking ability."
- "That attempt used typed mode."
- "Nothing is saved in this milestone — no history, no audio."

## Teacher-requirement evidence (30 s, after the app demo)

Show `docs/kanban.md`, `docs/sprint_backlog.md` priorities, the verified
GitHub Project board/issues, `docs/burndown.md`, and note US-13 CI
(`ci.yml` lint+test; `release.yml` versioned archive on tag; archive ≠
hosting) as the next required deliverable. No speech-model downloads or
credentials in tests.
