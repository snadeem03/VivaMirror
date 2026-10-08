# VivaMirror — Architecture (proposed, not yet implemented)

## Module map (planned)

```text
app/
├── main.py            # Streamlit entry: step router
│                      # (select → answer → review/edit → evaluate → retry/compare)
├── questions.py       # Loads curated bank (data/rubrics/*.json + schema validation)
├── rubrics.py         # Rubric model: concepts, weights, accepted phrases,
│                      # reference answers, follow-ups, rubric version
├── evaluate.py        # Deterministic matcher: phrase search + negation guard
│                      # → per-concept verdicts + evidence spans + coverage %
├── transcribe.py      # Adapter interface + default stub/local impl + typed passthrough
├── store.py           # SQLite persistence (attempts, history, progress queries)
└── ui_steps.py        # Streamlit step views (kept thin; no logic besides display)
data/
└── rubrics/           # 15 curated Distributed Systems entries (validated JSON)
tests/
└── ...                # Matcher, negation, math, schema, persistence (CI-safe)
```

No module outside `store.py` touches SQL; no module outside `evaluate.py`
decides covered/missed; no module outside `transcribe.py` touches audio.

## Data flow (one attempt)

```text
Question (+ rubric version)
  → Answer input: audio bytes ──▶ transcribe.Adapter ──▶ raw transcript ──┐
                  typed text ─────────────────────────────────────────────▶│ (either path)
  → Editable text (user reviews/edits; this exact text is evaluated)
  → evaluate.match(text, rubric) → [{concept, verdict, weight, evidence_span}]
  → coverage % = Σ(weights covered) / Σ(weights)
  → store.save(attempt: question, rubric_version, text, results, coverage, input_mode, ts)
  → UI renders covered vs. missed + evidence + disclaimer
  → Retry → second attempt → store → compare view (delta per concept + coverage)
```

## Separation of concerns

- **UI (`main.py`, `ui_steps.py`):** navigation and rendering only. Holds no
  matching logic, no SQL, no audio handling. Shows the honesty disclaimer and
  the input-mode label (audio vs. typed) on every result.
- **Rubric evaluation (`evaluate.py`, `rubrics.py`):** pure functions
  `text × rubric → verdicts`. No Streamlit, no I/O. Negation guard: before
  crediting a keyword/phrase hit, check a negation window (e.g. preceding
  tokens like "not / no / never / without / lacks / fails to") — a hit inside
  a negated span does not count. Unit-testable without any model or network.
- **Transcription (`transcribe.py`):** one interface,
  e.g. `transcribe(audio_bytes: bytes, mime: str) -> TranscriptionResult`,
  with swappable backends. Default tonight: stub/local free path that never
  requires a paid key; failures return a typed error the UI converts into
  "transcription unavailable — use typed mode". Audio bytes are transient
  (not written to disk, not stored in SQLite) unless the user explicitly opts in.
- **Persistence (`store.py`):** stdlib `sqlite3` only. Tables (planned):
  `attempts(id, question_id, rubric_version, input_mode, answer_text,
  coverage_pct, created_at)` and `concept_results(attempt_id, concept_id,
  verdict, evidence)`. DB file is local runtime data (git-ignored).

## How typed-answer mode keeps the core usable

Typed text enters the pipeline at the "editable text" stage, bypassing
`transcribe.py` entirely. Everything downstream (review/edit → evaluate →
persist → retry/compare) is input-agnostic: it operates on text + rubric.
Consequences:

1. The full evaluative loop (US-02/05/06/07/08) works with zero audio stack.
2. Transcription becomes an optional upstream text source, not a dependency.
3. The demo degrades honestly: if audio fails, the presenter states typed mode
   was used and the evaluation shown is still the real matcher.

## Primary delivery risk: speech setup

Microphone capture and transcription on Windows browsers is the top risk:
device permission prompts, HTTPS/localhost constraints, and the weight of
speech packages (which is why none are installed in M0). Mitigations: adapter
interface first, stub default, graceful-degrade UI, typed-mode-first demo
rehearsal, and a 30-minute timebox on audio work. If the timebox expires, audio
ships as "upload/stub + typed fallback" and the sprint still delivers its goal.

## What this architecture refuses

Login/accounts, model training, arbitrary document ingestion, paid-API
dependence, raw-audio retention by default, and any presentation of coverage as
correctness/confidence/intelligence/speaking ability. Agile tracking lives in
`docs/` and GitHub — never inside the practice UI.
