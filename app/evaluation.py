"""Evidence-based concept-coverage evaluator (US-06).

Pure Python, stdlib only: no LLM, no network, no speech model, no Streamlit.
The answer text is only ever sliced for evidence spans — never executed.

Vocabulary: this module reports *concept coverage* (share of rubric weight
with matched evidence). It never reports a "correctness score". A status of
``not_detected`` means the matcher found no evidence; it does not prove the
student does not know the concept.

Matching is deterministic and explainable: case-insensitive, whole-token,
consecutive-token matching of curated accepted phrases, with clause-aware
negation handling and curated contradiction indicators. See
``docs/evaluation.md`` for the rules and their documented limitations.
"""

from __future__ import annotations

import math
import re

COVERED = "covered"
NOT_DETECTED = "not_detected"
NEEDS_REVIEW = "needs_review"

# Bumped whenever matching/scoring semantics change. Stored attempts carry
# this so later comparisons can refuse deltas across versions instead of
# miscomparing historical results.
EVALUATOR_VERSION = "1"

DISCLAIMER = (
    "Concept coverage reflects matched rubric phrases shown as evidence; it is "
    "not a correctness, confidence, intelligence, or speaking-ability score. "
    "'Not detected' means the matcher found no evidence, not that you do not "
    "know the concept."
)

# Negation cues that can suppress a later phrase in the same clause segment.
# Words that legitimately occur *inside* accepted phrases (e.g. "not" in
# "smaller timestamp does not prove causation") are ignored when they fall
# inside the matched span itself; only cues *before* the match count.
_NEGATION_CUES = frozenset(
    {
        "not",
        "no",
        "never",
        "without",
        "cannot",
        "neither",
        "nor",
        "hardly",
        "barely",
        "scarcely",
        "lacking",
        "lacks",
        "lack",
        "lacked",
        "fails",
        "fail",
        "failed",
        "failing",
        "unable",
    }
)

# Contrast words start a fresh clause segment: negation before them does not
# carry over ("It is not consistent, but every request gets an answer").
_CONTRAST_WORDS = frozenset(
    {"but", "however", "although", "though", "whereas", "nevertheless",
     "nonetheless", "yet"}
)

# Tokens before a match that may carry a negating cue. A fixed window alone
# is not enough (hence clause segments and soft boundaries), but an unbounded
# lookback would let distant denials suppress real statements.
_NEGATION_WINDOW = 5

# Punctuation in the original text that bounds a negation scope without
# ending the sentence ("There is no master, and X takes over" still credits X).
_SOFT_BOUNDARIES = frozenset({",", ";", ":"})

# Small stopword set for contradiction matching against curated negative
# examples. Denial words (not/no/never/always/...) are deliberately kept:
# they are the distinctive part of most negative examples.
_NEG_STOPWORDS = frozenset(
    {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "to", "of", "in", "on", "and", "or", "it", "its", "this", "that",
        "these", "those", "with", "for", "as", "by", "at", "from", "into",
        "over", "under", "so", "such", "than", "then", "there", "their",
        "they", "them", "he", "she", "we", "you", "i", "my", "our", "your",
        "his", "her", "having", "has", "have", "had", "do", "does", "did",
        "will", "would", "can", "could", "should", "shall", "may", "might",
        "must",
    }
)

_CONTRACTION_REPLACEMENTS = (
    ("can't", "cannot"),
    ("won't", "will not"),
    ("it's", "it is"),
    ("n't", " not"),
    ("'re", " are"),
    ("'ve", " have"),
    ("'ll", " will"),
    ("'d", " would"),
    ("'m", " am"),
    # Possessive "'s" is dropped ("system's" -> "system"); it carries no
    # meaning the matcher needs and avoids a spurious "is" token.
    ("'s", ""),
)

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")
_SENTENCE_END_RE = re.compile(r"[.!?;\u2026]+|\n+")


class EvaluationError(ValueError):
    """Raised when the question or weights are structurally invalid."""


def _clean_text(text: str) -> str:
    """Lowercase and unify punctuation that must not affect matching."""
    return (
        text.lower()
        .replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\t", " ")
    )


def _expand_token(raw: str) -> list[str]:
    """Expand one raw token (e.g. "doesn't" -> ["does", "not"])."""
    for source, target in _CONTRACTION_REPLACEMENTS:
        if source in raw:
            return _split_expansion(raw, source, target)
    return [raw]


def _split_expansion(raw: str, source: str, target: str) -> list[str]:
    head, _, _ = raw.partition(source)
    words = [w for w in target.split(" ") if w]
    return ([head] if head else []) + words


def _tokenize_with_spans(original: str):
    """Tokenize answer text.

    Returns (tokens, norm_starts, norm_ends, orig_starts, orig_ends,
    soft_before, sent_index) as parallel lists: normalized word tokens with
    their spans in the normalized stream and in the ORIGINAL text, whether a
    soft-boundary punctuation precedes each token, and a sentence index.
    """
    cleaned = _clean_text(original)
    pieces: list[str] = []
    orig_spans: list[tuple[int, int]] = []
    soft_flags: list[bool] = []
    pending_soft = False
    pos = 0

    def emit(word: str, o_start: int, o_end: int) -> None:
        # Evidence slices use the original token span recorded here; expanded
        # words (e.g. "doesn't" -> "does", "not") share their source span.
        pieces.append(word)
        orig_spans.append((o_start, o_end))
        soft_flags.append(pending_soft)

    for match in _TOKEN_RE.finditer(cleaned):
        gap = cleaned[pos : match.start()]
        if any(ch in _SOFT_BOUNDARIES for ch in gap):
            pending_soft = True
        raw = match.group(0)
        for word in _expand_token(raw):
            emit(word, match.start(), match.end())
            pending_soft = False
        # A soft boundary directly attached after the token (e.g. "nodes,")
        # counts for the *next* token; handled via the gap above.
        pos = match.end()

    tokens = pieces
    # Sentence index per token from original-text boundaries.
    boundaries = [m.end() for m in _SENTENCE_END_RE.finditer(original)]
    sent_index: list[int] = []
    current = 0
    for o_start, _ in orig_spans:
        while current < len(boundaries) and o_start >= boundaries[current]:
            current += 1
        sent_index.append(current)
    return tokens, orig_spans, soft_flags, sent_index


def _normalize_phrase(phrase: str) -> list[str]:
    """Normalize an accepted phrase to word tokens (no offsets needed)."""
    words: list[str] = []
    for match in _TOKEN_RE.finditer(_clean_text(phrase)):
        words.extend(_expand_token(match.group(0)))
    return words


def _find_phrase(tokens: list[str], phrase_tokens: list[str]) -> list[tuple[int, int]]:
    """All whole-token consecutive occurrences; (start, end) token spans."""
    spans: list[tuple[int, int]] = []
    width = len(phrase_tokens)
    if not width or width > len(tokens):
        return spans
    for i in range(len(tokens) - width + 1):
        if tokens[i : i + width] == phrase_tokens:
            spans.append((i, i + width))
    return spans


def _clause_start(tokens: list[str], sent_index: list[int], pos: int) -> int:
    """Start of the current clause segment: sentence start or after contrast."""
    start = pos
    while start > 0 and sent_index[start - 1] == sent_index[pos]:
        start -= 1
    for i in range(pos - 1, start - 1, -1):
        if tokens[i] in _CONTRAST_WORDS:
            return i + 1
    return start


def _is_negated(
    tokens: list[str],
    soft_flags: list[bool],
    sent_index: list[int],
    match_start: int,
) -> bool:
    """Decide whether a phrase match is locally negated.

    Only cues in the same clause segment count: after the last contrast word,
    after the last soft-boundary punctuation, and within _NEGATION_WINDOW
    tokens. A "not" that belongs to "not only ... (but also ...)" is not a
    denial and is discounted.
    """
    seg_start = _clause_start(tokens, sent_index, match_start)
    lo = match_start
    for i in range(match_start - 1, seg_start - 1, -1):
        if soft_flags[i + 1]:
            lo = i + 1
            break
        lo = i
        if match_start - i > _NEGATION_WINDOW:
            break
    lo = max(lo, seg_start, match_start - _NEGATION_WINDOW)
    prefix = tokens[lo:match_start]
    for i, tok in enumerate(prefix):
        if tok == "not" and i + 1 < len(prefix) and prefix[i + 1] == "only":
            continue  # "not only ... but also ..." is affirmative
        if tok in _NEGATION_CUES:
            return True
    return False


def _neg_example_tokens(example: str) -> list[str]:
    return [t for t in _normalize_phrase(example) if t not in _NEG_STOPWORDS]


def _clause_ranges(
    tokens: list[str], sent_index: list[int]
) -> list[tuple[int, int]]:
    """Token ranges splitting sentences at contrast words (half-open)."""
    ranges: list[tuple[int, int]] = []
    i, n = 0, len(tokens)
    while i < n:
        j = i
        while (
            j + 1 < n
            and sent_index[j + 1] == sent_index[i]
            and tokens[j + 1] not in _CONTRAST_WORDS
        ):
            j += 1
        ranges.append((i, j + 1))
        i = j + 1
    return ranges


def _contradicting_clauses(
    tokens: list[str],
    orig_spans: list[tuple[int, int]],
    sent_index: list[int],
    neg_tokens: list[str],
    original: str,
) -> list[tuple[int, int]]:
    """Clauses whose content overlaps a negative example enough to count.

    A clause must share at least max(3, len(neg)-2) content tokens with the
    curated negative example. Returns original-text spans (trimmed).
    """
    if not neg_tokens:
        return []
    threshold = max(3, len(neg_tokens) - 2)
    neg_set = set(neg_tokens)
    hits: list[tuple[int, int]] = []
    for start, end in _clause_ranges(tokens, sent_index):
        content = {t for t in tokens[start:end] if t not in _NEG_STOPWORDS}
        if len(content & neg_set) >= threshold:
            o_start = orig_spans[start][0]
            o_end = orig_spans[end - 1][1]
            while o_start < o_end and original[o_start].isspace():
                o_start += 1
            while o_end > o_start and original[o_end - 1].isspace():
                o_end -= 1
            hits.append((o_start, o_end))
    return hits


def _require_question(question: object) -> dict:
    if not isinstance(question, dict):
        raise TypeError(
            f"question must be a dict (e.g. from load_question_bank), "
            f"got {type(question).__name__}"
        )
    qid = question.get("id")
    if not isinstance(qid, str) or not qid.strip():
        raise EvaluationError("question must have a nonempty string 'id'")
    concepts = question.get("concepts")
    if not isinstance(concepts, list) or not concepts:
        raise EvaluationError(
            f"question '{qid}': 'concepts' must be a nonempty list"
        )
    for i, concept in enumerate(concepts):
        where = f"question '{qid}': concepts[{i}]"
        if not isinstance(concept, dict):
            raise EvaluationError(f"{where} must be an object")
        for field in ("id", "label"):
            value = concept.get(field)
            if not isinstance(value, str) or not value.strip():
                raise EvaluationError(
                    f"{where}: '{field}' must be a nonempty string"
                )
        weight = concept.get("weight")
        if (
            isinstance(weight, bool)
            or not isinstance(weight, (int, float))
            or not math.isfinite(weight)
            or weight <= 0
        ):
            raise EvaluationError(
                f"{where}: 'weight' must be a positive finite number"
            )
        for field in ("accepted_phrases", "negative_examples"):
            phrases = concept.get(field)
            if (
                not isinstance(phrases, list)
                or not phrases
                or any(not isinstance(p, str) or not p.strip() for p in phrases)
            ):
                raise EvaluationError(
                    f"{where}: '{field}' must be a nonempty list of strings"
                )
    return question


def evaluate_answer(question: dict, answer: str) -> dict:
    """Evaluate one answer against one validated question's rubric.

    Returns a JSON-serializable dict with question id, concept-coverage
    percentage, per-concept findings (status, weights, evidence spans with
    original-text offsets, explanation), and the disclaimer.
    """
    question = _require_question(question)
    if not isinstance(answer, str):
        raise TypeError(
            f"answer must be a string, got {type(answer).__name__}"
        )
    original = answer
    concepts = question["concepts"]
    total = sum(float(c["weight"]) for c in concepts)
    if not math.isfinite(total) or total <= 0:
        raise EvaluationError("concept weights must sum to a positive number")

    if not original.strip():
        findings = [
            {
                "concept_id": c["id"],
                "label": c["label"],
                "weight": float(c["weight"]),
                "earned_weight": 0.0,
                "status": NOT_DETECTED,
                "evidence": [],
                "conflicting_evidence": [],
                "explanation": (
                    f"No answer text was provided, so no evidence for "
                    f"'{c['label']}' could be found."
                ),
            }
            for c in concepts
        ]
        return {
            "question_id": question["id"],
            "evaluator_version": EVALUATOR_VERSION,
            "coverage_pct": 0.0,
            "earned_weight": 0.0,
            "available_weight": total,
            "concepts": findings,
            "disclaimer": DISCLAIMER,
        }

    tokens, orig_spans, soft_flags, sent_index = _tokenize_with_spans(original)
    findings = []
    earned = 0.0
    for concept in concepts:
        weight = float(concept["weight"])
        supporting: list[dict] = []
        conflicting: list[dict] = []
        seen: set[tuple[int, int]] = set()
        for phrase in concept["accepted_phrases"]:
            phrase_tokens = _normalize_phrase(phrase)
            for ms, me in _find_phrase(tokens, phrase_tokens):
                o_start = orig_spans[ms][0]
                o_end = orig_spans[me - 1][1]
                if (o_start, o_end) in seen:
                    continue
                seen.add((o_start, o_end))
                entry = {
                    "text": original[o_start:o_end],
                    "start": o_start,
                    "end": o_end,
                    "matched_phrase": phrase,
                }
                if _is_negated(tokens, soft_flags, sent_index, ms):
                    conflicting.append(entry)
                else:
                    supporting.append(entry)
        for neg_example in concept["negative_examples"]:
            neg_tokens = _neg_example_tokens(neg_example)
            for o_start, o_end in _contradicting_clauses(
                tokens, orig_spans, sent_index, neg_tokens, original
            ):
                if (o_start, o_end) in seen:
                    continue
                seen.add((o_start, o_end))
                conflicting.append(
                    {
                        "text": original[o_start:o_end],
                        "start": o_start,
                        "end": o_end,
                        "matched_phrase": None,
                        "resembles": neg_example,
                    }
                )
        if supporting and not conflicting:
            status = COVERED
            earned_weight = weight
            earned += weight
            explanation = (
                f"Matched accepted phrase(s) for '{concept['label']}'; "
                f"awarded {weight:g} of {weight:g}."
            )
        elif supporting and conflicting:
            status = NEEDS_REVIEW
            earned_weight = 0.0
            explanation = (
                f"Both supporting and conflicting evidence found for "
                f"'{concept['label']}'; awarded 0 of {weight:g} until a "
                f"human judges which reading holds."
            )
        elif conflicting:
            status = NOT_DETECTED
            earned_weight = 0.0
            explanation = (
                f"Only negated or contradictory mention(s) of "
                f"'{concept['label']}' found; no weight awarded."
            )
        else:
            status = NOT_DETECTED
            earned_weight = 0.0
            explanation = (
                f"No accepted phrase for '{concept['label']}' found in the "
                f"answer; this means no evidence was detected, not that the "
                f"concept is unknown."
            )
        findings.append(
            {
                "concept_id": concept["id"],
                "label": concept["label"],
                "weight": weight,
                "earned_weight": earned_weight,
                "status": status,
                "evidence": supporting,
                "conflicting_evidence": conflicting,
                "explanation": explanation,
            }
        )
    coverage = 100.0 * earned / total
    return {
        "question_id": question["id"],
        "evaluator_version": EVALUATOR_VERSION,
        "coverage_pct": round(coverage, 1),
        "earned_weight": earned,
        "available_weight": total,
        "concepts": findings,
        "disclaimer": DISCLAIMER,
    }
