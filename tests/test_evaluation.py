"""Tests for the evidence-based concept evaluator (US-06).

Behavior-focused and CI-safe (stdlib only; no network, models, or UI).
Several tests use realistic viva answers against the REAL curated bank;
synthetic fixtures are used only where the bank has no suitable phrase
(e.g. contraction expansion). Assertions are strict: nothing is weakened
to make tests pass.
"""

import sys
from pathlib import Path

import pytest

from app.evaluation import (
    DISCLAIMER,
    EvaluationError,
    evaluate_answer,
)
from app.questions import load_question_bank


@pytest.fixture(scope="module")
def bank():
    return {q["id"]: q for q in load_question_bank()}


def _statuses(result):
    return {c["concept_id"]: c["status"] for c in result["concepts"]}


def _concept(result, cid):
    return next(c for c in result["concepts"] if c["concept_id"] == cid)


def _assert_spans_valid(result, original):
    for concept in result["concepts"]:
        for span in concept["evidence"] + concept["conflicting_evidence"]:
            assert original[span["start"] : span["end"]] == span["text"]
            assert span["text"].strip() == span["text"]
            assert span["start"] < span["end"]


# --- Empty input ---------------------------------------------------------------


def test_empty_answer_scores_zero(bank):
    result = evaluate_answer(bank["ds-15"], "")
    assert result["coverage_pct"] == 0.0
    assert result["earned_weight"] == 0.0
    assert result["available_weight"] == 100.0
    assert all(c["status"] == "not_detected" for c in result["concepts"])


def test_whitespace_answer_scores_zero(bank):
    result = evaluate_answer(bank["ds-15"], "   \n\t  ")
    assert result["coverage_pct"] == 0.0
    assert all(c["status"] == "not_detected" for c in result["concepts"])


# --- Full and partial coverage on the real bank ----------------------------------


FULL_DS15 = (
    "Since network splits will eventually happen, I must choose between "
    "consistency and availability; the trade-off applies during a partition. "
    "My CP design will refuse minority-side writes and reconcile divergent "
    "replicas afterwards, because without partitions all three hold and the "
    "pick-two slogan is misleading."
)

THIN_DS15 = "CAP is about distributed databases and partitions."


def test_full_supported_coverage_is_100(bank):
    result = evaluate_answer(bank["ds-15"], FULL_DS15)
    assert result["question_id"] == "ds-15"
    assert result["coverage_pct"] == 100.0
    assert result["earned_weight"] == 100.0
    assert all(c["status"] == "covered" for c in result["concepts"])
    assert all(c["earned_weight"] == c["weight"] for c in result["concepts"])
    _assert_spans_valid(result, FULL_DS15)


def test_thin_answer_scores_zero(bank):
    result = evaluate_answer(bank["ds-15"], THIN_DS15)
    assert result["coverage_pct"] == 0.0
    assert _statuses(result) == {
        "ds-15-c1": "not_detected",
        "ds-15-c2": "not_detected",
        "ds-15-c3": "not_detected",
        "ds-15-c4": "not_detected",
    }


def test_weighted_partial_coverage(bank):
    answer = (
        "Because network splits will eventually happen, I planned the "
        "partition behavior carefully. And remember: without partitions all "
        "three hold."
    )
    result = evaluate_answer(bank["ds-15"], answer)
    assert _statuses(result)["ds-15-c1"] == "covered"
    assert _statuses(result)["ds-15-c4"] == "covered"
    assert _statuses(result)["ds-15-c2"] == "not_detected"
    assert _statuses(result)["ds-15-c3"] == "not_detected"
    assert result["earned_weight"] == 45.0
    assert result["coverage_pct"] == 45.0
    _assert_spans_valid(result, answer)


def test_long_irrelevant_answer_scores_zero(bank):
    filler = (
        "Distributed systems are very important in modern computing and many "
        "students study them every semester with great interest. Networks, "
        "computers, servers, clients, protocols, messages, performance, and "
        "reliability all matter a great deal in practice, and examinations "
        "cover a wide syllabus with challenging material for everyone."
    )
    result = evaluate_answer(bank["ds-15"], filler)
    assert result["coverage_pct"] == 0.0
    assert result["earned_weight"] == 0.0


def test_single_keywords_earn_nothing(bank):
    result = evaluate_answer(bank["ds-13"], "quorum quorum quorum votes leader")
    assert result["coverage_pct"] == 0.0
    assert all(c["status"] == "not_detected" for c in result["concepts"])


# --- Normalization: case, punctuation, whitespace, contractions, tokens ----------


def test_case_punctuation_whitespace_tolerated(bank):
    answer = "A   COLLECTION of autonomous nodes,\nworking together as one."
    result = evaluate_answer(bank["ds-01"], answer)
    concept = _concept(result, "ds-01-c1")
    assert concept["status"] == "covered"
    assert concept["evidence"][0]["text"] == "COLLECTION of autonomous nodes"
    _assert_spans_valid(result, answer)


def test_hyphenated_words_match(bank):
    answer = "We do not use a single master. The highest-ID process takes over."
    result = evaluate_answer(bank["ds-13"], answer)
    concept = _concept(result, "ds-13-c3")
    assert concept["status"] == "covered"
    assert concept["evidence"][0]["text"] == "highest-ID process takes over"
    _assert_spans_valid(result, answer)


def _fixture_question():
    return {
        "id": "fx-01",
        "subject": "Distributed Systems",
        "topic": "Fixture",
        "difficulty": "foundational",
        "question_text": "Fixture?",
        "reference_answer": "Fixture.",
        "follow_up": "Fixture?",
        "concepts": [
            {
                "id": "fx-c1",
                "label": "Guarantee limits",
                "weight": 100,
                "explanation": "Fixture.",
                "accepted_phrases": ["cannot guarantee both properties"],
                "negative_examples": ["Both properties always hold together."],
            }
        ],
    }


def test_contraction_expansion_matches():
    result = evaluate_answer(
        _fixture_question(),
        "The system can't guarantee both properties during a split.",
    )
    assert _concept(result, "fx-c1")["status"] == "covered"


def test_token_boundaries_reject_substrings(bank):
    answer = "We keep photocopies on multiple nodes for the office printer."
    result = evaluate_answer(bank["ds-10"], answer)
    assert _concept(result, "ds-10-c1")["status"] == "not_detected"
    assert result["coverage_pct"] == 0.0


def test_repeated_phrases_award_weight_once(bank):
    once = "Copies on multiple nodes help availability."
    thrice = " ".join([once] * 3)
    first = evaluate_answer(bank["ds-10"], once)
    second = evaluate_answer(bank["ds-10"], thrice)
    assert _concept(first, "ds-10-c1")["earned_weight"] == 30.0
    assert second["earned_weight"] == first["earned_weight"]
    assert second["coverage_pct"] == first["coverage_pct"]
    _assert_spans_valid(second, thrice)


def test_evaluation_is_deterministic(bank):
    assert evaluate_answer(bank["ds-15"], FULL_DS15) == evaluate_answer(
        bank["ds-15"], FULL_DS15
    )


# --- Negation and contradiction ---------------------------------------------------


def test_negated_positive_assertion_gets_no_credit(bank):
    answer = "Our design does not insist it wins only with a quorum of votes."
    result = evaluate_answer(bank["ds-13"], answer)
    concept = _concept(result, "ds-13-c3")
    assert concept["status"] == "not_detected"
    assert concept["earned_weight"] == 0.0
    assert concept["conflicting_evidence"][0]["text"] == (
        "wins only with a quorum of votes"
    )
    _assert_spans_valid(result, answer)


def test_preceding_negative_sentence_does_not_suppress_next(bank):
    answer = (
        "We do not use a single master. "
        "The highest-ID process takes over after a crash."
    )
    result = evaluate_answer(bank["ds-13"], answer)
    concept = _concept(result, "ds-13-c3")
    assert concept["status"] == "covered"
    assert concept["earned_weight"] == 25.0
    _assert_spans_valid(result, answer)


def test_comma_bounded_negation_does_not_carry_over(bank):
    answer = (
        "There is no single master, and the highest-ID process takes over."
    )
    result = evaluate_answer(bank["ds-13"], answer)
    assert _concept(result, "ds-13-c3")["status"] == "covered"


def test_contrast_clause_after_but_is_credited(bank):
    answer = (
        "The store is not consistent, but it will refuse requests or answer "
        "from one side during splits."
    )
    result = evaluate_answer(bank["ds-15"], answer)
    concept = _concept(result, "ds-15-c2")
    assert concept["status"] == "covered"
    assert concept["earned_weight"] == 35.0
    _assert_spans_valid(result, answer)


def test_negative_form_concept_stays_eligible_lamport(bank):
    answer = (
        "A smaller timestamp does not prove causation, since concurrent "
        "events are ordered arbitrarily."
    )
    result = evaluate_answer(bank["ds-08"], answer)
    concept = _concept(result, "ds-08-c4")
    assert concept["status"] == "covered"
    assert concept["earned_weight"] == 20.0
    _assert_spans_valid(result, answer)


def test_not_only_but_also_is_affirmative():
    question = {
        "id": "fx-02",
        "subject": "Distributed Systems",
        "topic": "Fixture",
        "difficulty": "foundational",
        "question_text": "Fixture?",
        "reference_answer": "Fixture.",
        "follow_up": "Fixture?",
        "concepts": [
            {
                "id": "fx-c1",
                "label": "Convergence",
                "weight": 100,
                "explanation": "Fixture.",
                "accepted_phrases": ["replicas converge after writes stop"],
                "negative_examples": ["Replicas never agree without any mechanism."],
            }
        ],
    }
    answer = (
        "The design ensures not only that replicas converge after writes "
        "stop but also fast local reads."
    )
    result = evaluate_answer(question, answer)
    assert _concept(result, "fx-c1")["status"] == "covered"


def test_supporting_plus_conflicting_gives_needs_review(bank):
    answer = (
        "Copies on multiple nodes help availability, but we do not keep "
        "copies on multiple nodes for this table."
    )
    result = evaluate_answer(bank["ds-10"], answer)
    concept = _concept(result, "ds-10-c1")
    assert concept["status"] == "needs_review"
    assert concept["earned_weight"] == 0.0
    assert len(concept["evidence"]) == 1
    assert len(concept["conflicting_evidence"]) == 1
    _assert_spans_valid(result, answer)


def test_contradicting_negative_example_flags_conflict(bank):
    answer = "In our design, network partitions can be prevented entirely."
    result = evaluate_answer(bank["ds-15"], answer)
    concept = _concept(result, "ds-15-c1")
    assert concept["status"] == "not_detected"
    assert concept["earned_weight"] == 0.0
    assert concept["conflicting_evidence"], "expected contradiction evidence"
    _assert_spans_valid(result, answer)


def test_valid_paraphrase_outside_phrase_list_stays_undetected():
    # Honest limitation, asserted as specified: semantic paraphrases without
    # any accepted phrase must remain not_detected.
    answer = (
        "When the network breaks, you cannot have both perfect agreement "
        "and always-on responses."
    )
    bank = load_question_bank()
    question = next(q for q in bank if q["id"] == "ds-15")
    result = evaluate_answer(question, answer)
    assert _concept(result, "ds-15-c2")["status"] == "not_detected"
    assert result["coverage_pct"] == 0.0


# --- Output contract and invalid inputs ---------------------------------------------


def test_result_uses_coverage_language_not_correctness(bank):
    result = evaluate_answer(bank["ds-15"], FULL_DS15)
    assert "coverage_pct" in result
    assert "correctness score" not in str(result).lower()
    assert result["disclaimer"] == DISCLAIMER
    assert "not a correctness" in result["disclaimer"]


def test_coverage_math_is_exact(bank):
    answer = (
        "Because network splits will eventually happen. Also, without "
        "partitions all three hold."
    )
    result = evaluate_answer(bank["ds-15"], answer)
    assert result["earned_weight"] == 45.0
    assert result["available_weight"] == 100.0
    assert result["coverage_pct"] == round(100 * 45.0 / 100.0, 1)


@pytest.mark.parametrize("bad", [123, None, ["text"], b"bytes"])
def test_non_string_answer_rejected(bank, bad):
    with pytest.raises(TypeError, match="must be a string"):
        evaluate_answer(bank["ds-15"], bad)


@pytest.mark.parametrize(
    "bad",
    ["not-a-dict", [], None, {}, {"id": "  ", "concepts": []}],
)
def test_malformed_question_rejected(bad):
    with pytest.raises((TypeError, EvaluationError)):
        evaluate_answer(bad, "some answer text")


def test_question_with_bad_weight_rejected():
    question = _fixture_question()
    question["concepts"][0]["weight"] = True
    with pytest.raises(EvaluationError, match="weight"):
        evaluate_answer(question, "cannot guarantee both properties")


def test_evaluator_has_no_ui_speech_or_network_dependencies():
    # Fresh interpreter: importing/using the evaluator must not pull the UI,
    # speech, or network stacks (order-independent, unlike sys.modules).
    import subprocess

    root = Path(__file__).resolve().parent.parent
    code = (
        "import sys; from app.questions import load_question_bank; "
        "from app.evaluation import evaluate_answer; "
        "qs = {q['id']: q for q in load_question_bank()}; "
        "evaluate_answer(qs['ds-01'], 'A collection of autonomous nodes.'); "
        "bad = [m for m in ('streamlit', 'torch', 'whisper', "
        "'faster_whisper', 'requests') if m in sys.modules]; "
        "assert not bad, 'forbidden imports: ' + ','.join(bad); "
        "print('evaluator import clean')"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
