# VivaMirror — Evaluator (US-06): matching, scoring, and limitations

Implementation: `app/evaluation.py` (pure Python, stdlib only).
Tests: `tests/test_evaluation.py` (35 tests, several on the real bank).

## What the evaluator does

`evaluate_answer(question, answer_text)` matches the question's curated
accepted phrases against the student's (possibly edited) answer and reports
**concept coverage**: the share of rubric weight with matched evidence.

Output per question: question ID, `coverage_pct`, earned/available weights,
per-concept findings, and a disclaimer. Per concept: status (`covered`,
`not_detected`, `needs_review`), earned weight, exact evidence quoted from
the ORIGINAL answer with original-text `start`/`end` offsets, conflicting
evidence where found, and a plain-language explanation.

## Matching and scoring

- **Case-insensitive, whole-token, consecutive-token matching.** "Quorum"
  matches "quorum" but never the inside of "quorums"; "highest-ID" matches
  "highest ID" because hyphens normalize to spaces.
- **Normalization tolerated:** case, punctuation, extra whitespace, newlines,
  and common contractions ("can't" → "cannot", "doesn't" → "does not").
- **Offsets stay reliable:** tokens are located in the original text first;
  normalization only decides *equality*. Every span satisfies
  `answer[start:end] == text`, asserted by tests across mixed-case,
  punctuated, and hyphenated answers.
- **Weight at most once:** repeating a phrase lists more evidence spans but
  never increases the score; long irrelevant answers score 0.
- **No single-keyword credit:** "quorum quorum quorum" earns nothing — only
  full multi-word accepted phrases count.
- **Scoring:** `coverage = 100 * earned_weight / total_weight` computed on
  unrounded values; only `covered` concepts earn weight. Empty/whitespace
  answers yield zero detected coverage (all `not_detected`), never an error.
  Presentation rounds `coverage_pct` to one decimal, consistently.
- **Deterministic and explainable:** same inputs → same outputs; every credit
  names the matched phrase and shows the evidence. The answer text is only
  sliced, never executed. Invalid types raise clear errors (`TypeError` for a
  non-string answer or non-dict question, `EvaluationError` for bad structure
  or weights).

## Negation and contradiction rules (clause-aware, conservative)

A fixed word-window alone is not used. For each match, only cues in the same
clause segment count: after the last contrast word (`but`, `however`,
`although`, …), after the last soft boundary (comma/semicolon/colon), and
within 5 tokens before the match.

- A locally negated positive assertion ("does not insist it wins only with a
  quorum of votes") earns **no credit**; the negated span is kept as
  conflicting evidence, status `not_detected`.
- Negation **does not cross sentence boundaries**: "We do not use a single
  master. The highest-ID process takes over." still credits the second
  sentence. Commas also bound scope ("There is no master, and X takes over"
  credits X).
- Contrast resets scope: "…not consistent, **but** it will refuse requests or
  answer from one side…" credits the clause after "but".
- Correct negative-form concepts stay eligible: negation cues *inside* the
  matched span belong to the claim itself, so "A smaller timestamp does not
  prove causation" is `covered` for ds-08-c4.
- "Not only … but also …" is affirmative: the "not" in "not only" is
  discounted, so both branches can earn credit.
- Curated `negative_examples` are **contradiction indicators, not a complete
  detector**: a clause sharing at least `max(3, len-2)` content tokens with a
  negative example counts as conflicting evidence.
- **Both supporting and conflicting evidence → `needs_review`, zero weight**,
  both spans shown. Uncertain readings resolve to `needs_review` or
  `not_detected` — never to confident credit.

## Unsupported paraphrases and false positives (honest limits)

- A semantically valid paraphrase with **no accepted phrase stays
  `not_detected`** (tested: "When the network breaks, you cannot have both
  perfect agreement and always-on responses" scores 0 on ds-15). The matcher
  has no synonyms, stemming, or semantic understanding — vocabulary outside
  the rubric is invisible to it, and the UI must say so.
- Refuting a misconception in words close to a negative example can flag
  conflicting evidence; quotes and "some claim X, but actually…" constructions
  are not understood as such.
- Double negations, distant cues past the 5-token window, and unusual
  contrast markers can mis-scope. Direction of error is conservative (missed
  credit or `needs_review`, not false credit).
- There is **no general language reasoning** here — only token matching plus
  the rules above. Anything subtler belongs to a human marker.

## Why coverage is not correctness

A `covered` verdict means: the answer contained rubric vocabulary in
non-negated form. It does **not** mean the explanation is right, complete,
well-reasoned, confidently delivered, or intelligently argued — a fluent,
confident, entirely wrong answer that happens to use the phrases still
matches. Conversely `not_detected` never proves ignorance. The shipped
disclaimer states this on every result, and the product must never present
coverage as a grade of correctness, confidence, intelligence, or speaking
ability.

## How UI users should interpret `needs_review`

`needs_review` means the matcher found evidence pulling both ways (e.g. the
phrase stated and denied) and awarded **zero** weight for that concept. It is
a request for human judgment, not a partial mark: re-read the two quoted
spans, decide which reading reflects the student's understanding, and treat
the coverage number as provisional until then.
