# VivaMirror — Demo Plan (tonight's MVP)

Total: ~5 minutes. One question, two attempts, one comparison. State the input
mode aloud every time it matters.

## Setup (before audience)

- App running via documented command (`py -3.11 -m streamlit run app/main.py`).
- One curated Distributed Systems question chosen (e.g. quorum / CAP /
  leader election — whichever rubric is most complete).
- History empty (fresh local DB) so attempt 1 vs. attempt 2 is unambiguous.

## Act 1 — One incomplete answer → missed concepts (2 min)

1. Select the question; show prompt + that typed mode is being used
   (say: "typed mode — transcription bypassed").
2. Enter a deliberately thin answer covering ~1 of 4–5 concepts
   (e.g. mention "replication" but omit quorum, consistency trade-offs,
   failure handling).
3. Show the editable-transcript step; keep text as-is.
4. Evaluate. Point at: covered concept(s) WITH quoted evidence spans, missed
   concepts with weights, coverage % (low), and the disclaimer that coverage
   is rubric-phrase presence — not correctness, confidence, intelligence, or
   speaking ability.

Expected: low coverage, explicit missed list.

## Act 2 — One improved answer → increased coverage (1.5 min)

1. Hit Retry (same question, same rubric version).
2. Enter an improved answer that adds the previously missed concepts in own
   words (use accepted-phrase-adjacent wording from the rubric).
3. Evaluate. Point at: previously missed concepts now covered with new
   evidence spans, higher coverage %.

Expected: strictly higher coverage; delta visible per concept.
Include one negated sentence in rehearsal (e.g. "the system does not use
quorum") to show it earns no credit — mention the negation guard briefly.

## Act 3 — Retry comparison (1 min)

1. Open the comparison/history view: attempt 1 vs. attempt 2 side by side —
   coverage %, per-concept delta, timestamps, input mode labels.
2. Note persistence: attempts are in local SQLite; raw audio retained nowhere.

## Act 4 — Real audio transcription when available (0.5 min, conditional)

- **If the audio path works live:** record/upload a short spoken version of
  the improved answer, show the transcript in the editable step, correct one
  word by hand (demonstrating review/edit), evaluate.
- **If it does not work live:** say so explicitly —
  "audio path unsupported in this environment; typed mode shown instead; the
  transcription adapter interface exists and defaults to no paid API."
  Never fake a transcription.

## Fallback lines (honesty script)

- "Coverage counts rubric concepts evidenced in the text — it is not a grade
  of correctness, confidence, intelligence, or speaking ability."
- "That attempt used typed mode" / "That attempt used transcribed audio."
- "Raw audio is not retained by default."

## Teacher-requirement evidence (30 s, after the app demo)

Show `docs/kanban.md`, `docs/sprint_backlog.md` priorities, the GitHub Project
board/issues (or the setup blocker + exact commands if auth is still missing),
and note the CI plan (`ci.yml` lint+test; `release.yml` versioned archive on
tag; archive ≠ hosting). No speech-model downloads or credentials in tests.
