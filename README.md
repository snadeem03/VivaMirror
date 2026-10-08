# VivaMirror — A Practice Viva That Shows What You Missed

> **Milestone 0 status: planning only — application is NOT implemented yet.**
> This commit contains scope, backlog, sprint plan, Kanban, architecture,
> demo plan, and progress-event scaffolding. No application code exists.

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
2. Answer by **recording / uploading audio where supported**, OR by
   **typing the answer** (typed mode works independently of transcription).
3. Transcribe audio through a **replaceable transcription adapter**
   (no paid API by default).
4. **Review and edit** the transcript before evaluation.
5. Evaluate against a **curated rubric**: required concepts, weights,
   accepted phrases, reference answer, follow-up questions.
6. See **covered vs. missed concepts** with matched evidence phrases.
7. **Retry** the question; **compare attempts** (SQLite history + progress view).

## 4. MVP scope (tonight, ~5-hour accelerated student sprint)

Included:

- Streamlit interface, Python 3.11.
- Distributed Systems only, 15 curated questions + rubrics
  (concepts, weights, accepted phrases, reference answers, follow-ups).
- Microphone recording / audio upload where the browser/OS supports it.
- Replaceable transcription adapter (default: free/local, no paid API).
- Typed-answer mode, usable even when transcription is unavailable.
- Editable transcript before evaluation.
- Transparent concept-coverage feedback with matched evidence spans.
- Negation-safe matching: negated phrases (e.g. "not consistent",
  "never uses quorum") must NOT earn credit merely for containing a keyword.
- SQLite attempt history + retry comparison.
- No login, no model training, no arbitrary document ingestion.

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
  ability. The UI must say so.
- **Rubric-bound.** Feedback quality is limited to 15 hand-curated rubrics;
  paraphrases outside the accepted-phrase lists may be missed.
- **Transcription risk.** Microphone/transcription is the primary delivery
  risk on Windows browsers (permissions, device support, model availability).
  Typed-answer mode exists precisely so the core loop stays usable.
- **Local-only.** History lives in a local SQLite file; raw audio is NOT
  retained by default (privacy by default).
- **Tonight's build is a practice aid**, not an examiner or grading authority.

## 8. Repository layout (planned — files do not exist yet except docs)

```text
VivaMirror/
├── README.md
├── docs/
│   ├── product_backlog.md
│   ├── sprint_backlog.md
│   ├── kanban.md
│   ├── progress_events.jsonl
│   ├── architecture.md
│   └── demo_plan.md
├── .github/workflows/      # planned in CI milestone (not yet implemented)
├── app/                    # planned (not yet implemented)
├── data/rubrics/           # planned: 15 curated Distributed Systems rubrics
├── tests/                  # planned: meaningful, credential-free tests
└── .gitignore
```

## 9. Agile tracking (teacher requirements)

- Kanban board: `docs/kanban.md` (local mirror) + GitHub Project board
  (once `gh` auth is available — see sprint backlog §7 for the blocker).
- Sprint backlog: `docs/sprint_backlog.md` (one accelerated student
  development sprint, ~5 h estimate, start timestamp + timezone).
- User-story priorities: `docs/product_backlog.md` (P0/P1/P2).
- Burndown: derived from `docs/progress_events.jsonl`
  (append-only; ISO timestamps with timezone + remaining-minutes estimates).
- CI/CD in GitHub Actions: planned (lint+test; versioned archive on tag),
  implemented in the later CI milestone — not in Milestone 0.

## 10. How to verify Milestone 0

```powershell
git -C "D:\-_-\VivaMirror" status
git -C "D:\-_-\VivaMirror" log --oneline -5
Get-ChildItem "D:\-_-\VivaMirror\docs"
```

Expected: one planning commit `docs: initialize VivaMirror scope and sprint plan`,
clean tree, no application code, no installed speech packages.
