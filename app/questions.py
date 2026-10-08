"""Curated question-bank loader and validation (US-10).

Stdlib only. Imports neither Streamlit nor any speech model, so the bank is
usable from tests, CI, and any future UI without extra dependencies.

Matching these rubrics against free text is a job for the future evaluator
(US-06): a matched phrase is rubric evidence, never proof of correctness,
and this module implements no negation detection at all.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

EXPECTED_QUESTION_COUNT = 15
EXPECTED_WEIGHT_TOTAL = 100
EXPECTED_SUBJECT = "Distributed Systems"
ALLOWED_DIFFICULTIES = ("foundational", "intermediate", "advanced")
MIN_CONCEPTS = 3
MAX_CONCEPTS = 5

_QUESTION_STRING_FIELDS = (
    "id",
    "subject",
    "topic",
    "difficulty",
    "question_text",
    "reference_answer",
    "follow_up",
)

_CONCEPT_STRING_FIELDS = ("id", "label", "explanation")


class QuestionBankError(ValueError):
    """Raised when the curated question bank fails validation."""


def default_bank_path() -> Path:
    """Absolute path of the curated bank, independent of the working directory."""
    return Path(__file__).resolve().parent.parent / "data" / "questions.json"


def load_bank_file(path: str | Path | None = None) -> object:
    """Read and JSON-parse the bank file.

    Raises:
        FileNotFoundError: with the resolved path when the file is missing.
        QuestionBankError: when the file is not valid JSON.
    """
    resolved = Path(path).expanduser() if path is not None else default_bank_path()
    try:
        text = resolved.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"question bank not found: {resolved}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise QuestionBankError(
            f"question bank is not valid JSON: {resolved}: {exc}"
        ) from exc


def _require_nonempty_string(mapping: dict, field: str, where: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        raise QuestionBankError(
            f"{where}: field '{field}' must be a nonempty string, "
            f"got {value!r}"
        )
    return value


def _validate_weight(weight: object, where: str) -> float:
    # bool is a subclass of int: reject explicitly so True/False never count.
    if isinstance(weight, bool) or not isinstance(weight, (int, float)):
        raise QuestionBankError(
            f"{where}: field 'weight' must be a positive finite number, "
            f"got {weight!r}"
        )
    if not math.isfinite(weight) or weight <= 0:
        raise QuestionBankError(
            f"{where}: field 'weight' must be a positive finite number, "
            f"got {weight!r}"
        )
    return float(weight)


def _validate_concept(concept: object, question_id: str, index: int) -> dict:
    where = f"question '{question_id}': concepts[{index}]"
    if not isinstance(concept, dict):
        raise QuestionBankError(f"{where} must be an object, got {concept!r}")
    for field in _CONCEPT_STRING_FIELDS:
        _require_nonempty_string(concept, field, where)
    weight = _validate_weight(concept.get("weight"), where)

    for list_field in ("accepted_phrases", "negative_examples"):
        phrases = concept.get(list_field)
        if not isinstance(phrases, list) or not phrases:
            raise QuestionBankError(
                f"{where}: field '{list_field}' must be a nonempty list, "
                f"got {phrases!r}"
            )
        for i, phrase in enumerate(phrases):
            if not isinstance(phrase, str) or not phrase.strip():
                raise QuestionBankError(
                    f"{where}: field '{list_field}[{i}]' must be a nonempty "
                    f"string, got {phrase!r}"
                )
        if list_field == "accepted_phrases":
            for i, phrase in enumerate(phrases):
                # Single loose words award credit accidentally; accepted
                # phrases must be meaningful multi-word phrases.
                if len(phrase.split()) < 2:
                    raise QuestionBankError(
                        f"{where}: field 'accepted_phrases[{i}]' must be a "
                        f"meaningful phrase (at least two words), "
                        f"got {phrase!r}"
                    )
    concept["weight"] = weight
    return concept


def _validate_question(question: object, index: int) -> dict:
    where = f"questions[{index}]"
    if not isinstance(question, dict):
        raise QuestionBankError(f"{where} must be an object, got {question!r}")
    for field in _QUESTION_STRING_FIELDS:
        _require_nonempty_string(question, field, where)

    question_id = question["id"]
    where = f"question '{question_id}'"
    if question["subject"] != EXPECTED_SUBJECT:
        raise QuestionBankError(
            f"{where}: field 'subject' must be {EXPECTED_SUBJECT!r}, "
            f"got {question['subject']!r}"
        )
    if question["difficulty"] not in ALLOWED_DIFFICULTIES:
        raise QuestionBankError(
            f"{where}: field 'difficulty' must be one of "
            f"{list(ALLOWED_DIFFICULTIES)}, got {question['difficulty']!r}"
        )

    concepts = question.get("concepts")
    if not isinstance(concepts, list) or not (
        MIN_CONCEPTS <= len(concepts) <= MAX_CONCEPTS
    ):
        raise QuestionBankError(
            f"{where}: field 'concepts' must be a list of "
            f"{MIN_CONCEPTS} to {MAX_CONCEPTS} concepts, "
            f"got {concepts!r}"
            if not isinstance(concepts, list)
            else f"{where}: field 'concepts' must hold {MIN_CONCEPTS} to "
            f"{MAX_CONCEPTS} concepts, got {len(concepts)}"
        )
    validated = [
        _validate_concept(concept, question_id, i)
        for i, concept in enumerate(concepts)
    ]
    concept_ids = [c["id"] for c in validated]
    if len(set(concept_ids)) != len(concept_ids):
        raise QuestionBankError(
            f"{where}: concept IDs must be unique, got {concept_ids}"
        )
    total = sum(c["weight"] for c in validated)
    if not math.isclose(total, EXPECTED_WEIGHT_TOTAL, abs_tol=1e-6):
        raise QuestionBankError(
            f"{where}: concept weights must sum to {EXPECTED_WEIGHT_TOTAL}, "
            f"got {total}"
        )
    question["concepts"] = validated
    return question


def validate_bank(data: object) -> list[dict]:
    """Validate parsed bank data, returning the question list.

    Raises:
        QuestionBankError: identifying the invalid question/field.
    """
    if not isinstance(data, list):
        raise QuestionBankError(
            f"question bank must be a list of questions, got "
            f"{type(data).__name__}"
        )
    if len(data) != EXPECTED_QUESTION_COUNT:
        raise QuestionBankError(
            f"curated bank must hold exactly {EXPECTED_QUESTION_COUNT} "
            f"questions, got {len(data)}"
        )
    questions = [_validate_question(q, i) for i, q in enumerate(data)]
    question_ids = [q["id"] for q in questions]
    if len(set(question_ids)) != len(question_ids):
        raise QuestionBankError(
            f"question IDs must be unique, got {question_ids}"
        )
    return questions


def load_question_bank(path: str | Path | None = None) -> list[dict]:
    """Load the curated bank from disk and validate it.

    Defaults to ``data/questions.json`` resolved from this file's location,
    so callers work from any working directory.
    """
    return validate_bank(load_bank_file(path))
