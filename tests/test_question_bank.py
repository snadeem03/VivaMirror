"""Tests for the curated question-bank loader and validation (US-10).

Behavior-focused, CI-safe (no network, models, or credentials). Fixtures are
written to temporary directories; the real curated bank is only ever read.
"""

import copy
import json
import sys

import pytest

from app.questions import (
    EXPECTED_QUESTION_COUNT,
    QuestionBankError,
    load_bank_file,
    load_question_bank,
    validate_bank,
)

CURATED_COUNT = EXPECTED_QUESTION_COUNT


def _concept(cid="t-c1", weight=50):
    return {
        "id": cid,
        "label": "Test concept",
        "weight": weight,
        "explanation": "Why this concept matters.",
        "accepted_phrases": ["meaningful test phrase one", "another valid phrase here"],
        "negative_examples": ["The system does not use this mechanism at all."],
    }


def _question(qid="t-01", n_concepts=3, weights=(40, 35, 25)):
    return {
        "id": qid,
        "subject": "Distributed Systems",
        "topic": "Test topic",
        "difficulty": "foundational",
        "question_text": "What is the test concept?",
        "reference_answer": "A concise reference answer.",
        "concepts": [
            _concept(f"{qid}-c{i + 1}", w)
            for i, w in enumerate(list(weights)[:n_concepts])
        ],
        "follow_up": "What is the follow-up question?",
    }


def _bank(n=CURATED_COUNT, **kwargs):
    return [_question(f"t-{i + 1:02d}", **kwargs) for i in range(n)]


def _write(tmp_path, data):
    path = tmp_path / "bank.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# --- Valid bank -------------------------------------------------------------


def test_valid_curated_bank_loads_from_repo_default():
    questions = load_question_bank()
    assert len(questions) == CURATED_COUNT
    ids = [q["id"] for q in questions]
    assert len(set(ids)) == CURATED_COUNT
    for q in questions:
        assert 3 <= len(q["concepts"]) <= 5
        total = sum(c["weight"] for c in q["concepts"])
        assert total == pytest.approx(100.0)
        for concept in q["concepts"]:
            assert len(concept["accepted_phrases"]) >= 1


def test_valid_fixture_bank_passes_validation(tmp_path):
    questions = validate_bank(_bank())
    assert len(questions) == CURATED_COUNT
    assert load_question_bank(_write(tmp_path, _bank())) == questions


# --- Duplicate IDs -----------------------------------------------------------


def test_duplicate_question_ids_rejected():
    data = _bank()
    data[1]["id"] = data[0]["id"]
    with pytest.raises(QuestionBankError, match="unique"):
        validate_bank(data)


def test_duplicate_concept_ids_within_question_rejected():
    data = _bank()
    data[0]["concepts"][1]["id"] = data[0]["concepts"][0]["id"]
    with pytest.raises(QuestionBankError, match="unique"):
        validate_bank(data)


# --- Missing / mistyped fields -------------------------------------------------


def test_wrong_bank_count_rejected():
    with pytest.raises(QuestionBankError, match="exactly 15"):
        validate_bank(_bank(n=14))


def test_non_list_bank_rejected():
    with pytest.raises(QuestionBankError, match="must be a list"):
        validate_bank({"id": "not-a-list"})


@pytest.mark.parametrize("field", ["topic", "reference_answer", "follow_up"])
def test_missing_question_field_rejected(field):
    data = _bank()
    del data[3][field]
    with pytest.raises(QuestionBankError, match=field):
        validate_bank(data)


def test_empty_question_text_rejected():
    data = _bank()
    data[0]["question_text"] = "   "
    with pytest.raises(QuestionBankError, match="question_text"):
        validate_bank(data)


def test_concepts_wrong_type_rejected():
    data = _bank()
    data[0]["concepts"] = "not-a-list"
    with pytest.raises(QuestionBankError, match="concepts"):
        validate_bank(data)


def test_too_few_concepts_rejected():
    data = _bank(n_concepts=2, weights=(50, 50))
    with pytest.raises(QuestionBankError, match="concepts"):
        validate_bank(data)


def test_missing_concept_explanation_rejected():
    data = _bank()
    del data[0]["concepts"][0]["explanation"]
    with pytest.raises(QuestionBankError, match="explanation"):
        validate_bank(data)


def test_single_word_accepted_phrase_rejected():
    data = _bank()
    data[0]["concepts"][0]["accepted_phrases"] = ["quorum"]
    with pytest.raises(QuestionBankError, match="accepted_phrases"):
        validate_bank(data)


# --- Invalid weights ------------------------------------------------------------


@pytest.mark.parametrize("bad", [0, -5, True, False, "25", None, float("nan"), float("inf")])
def test_invalid_weights_rejected(bad):
    data = _bank()
    data[0]["concepts"][0]["weight"] = bad
    with pytest.raises(QuestionBankError, match="weight"):
        validate_bank(data)


def test_weight_sum_must_total_100():
    data = _bank(n_concepts=3, weights=(50, 30, 30))
    with pytest.raises(QuestionBankError, match="sum to 100"):
        validate_bank(data)


# --- File handling ---------------------------------------------------------------


def test_malformed_json_rejected(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"not": "a list"', encoding="utf-8")
    with pytest.raises(QuestionBankError, match="not valid JSON"):
        load_question_bank(path)


def test_missing_file_reports_path(tmp_path):
    missing = tmp_path / "absent.json"
    with pytest.raises(FileNotFoundError, match="absent.json"):
        load_question_bank(missing)


def test_loading_works_from_another_working_directory(tmp_path, monkeypatch):
    path = _write(tmp_path, _bank())
    monkeypatch.chdir(tmp_path)
    assert len(load_question_bank(path)) == CURATED_COUNT


def test_default_path_resolves_independent_of_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert len(load_question_bank()) == CURATED_COUNT


# --- Loader hygiene -----------------------------------------------------------------


def test_loader_pulls_in_no_streamlit_or_speech_stack():
    for module in ("streamlit", "torch", "whisper", "faster_whisper"):
        assert module not in sys.modules, f"{module} must not be imported"


def test_error_names_the_offending_question_and_field():
    data = _bank()
    data[7]["concepts"][1]["weight"] = -1
    with pytest.raises(QuestionBankError) as excinfo:
        validate_bank(data)
    message = str(excinfo.value)
    assert "t-08" in message and "weight" in message


def test_real_bank_file_is_not_modified_by_validation(tmp_path):
    before = load_bank_file()
    snapshot = copy.deepcopy(before)
    validate_bank(before)
    assert load_bank_file() == snapshot
