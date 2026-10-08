"""Tests for the practice-flow state machine (US-01/US-02/US-05 slice).

Pure helper tests: no Streamlit involved. UI-level coverage lives in
tests/test_ui.py via AppTest.
"""

import pytest

from app import flow
from app.questions import load_question_bank


@pytest.fixture(scope="module")
def bank():
    return {q["id"]: q for q in load_question_bank()}


def test_initial_state_is_empty():
    state = flow.initial_state()
    assert state["question_id"] is None
    assert state["draft"] == ""
    assert state["reviewed"] == ""
    assert state["result"] is None
    assert state["stage"] == flow.STAGE_ANSWER
    assert not flow.can_view_reference(state)


def test_select_question_resets_stale_data(bank):
    state = flow.initial_state()
    flow.select_question(state, "ds-15")
    flow.update_draft(state, "some draft")
    assert flow.submit_for_review(state)
    assert flow.confirm_evaluation(state, bank["ds-15"])
    assert state["result"] is not None

    flow.select_question(state, "ds-08")
    assert state["question_id"] == "ds-08"
    assert state["draft"] == ""
    assert state["reviewed"] == ""
    assert state["result"] is None
    assert state["stage"] == flow.STAGE_ANSWER
    assert not flow.can_view_reference(state)


def test_select_question_rejects_blank_id():
    with pytest.raises(flow.FlowError):
        flow.select_question(flow.initial_state(), "   ")


def test_draft_review_evaluation_transition(bank):
    state = flow.initial_state()
    flow.select_question(state, "ds-01")
    flow.update_draft(state, "A collection of autonomous nodes.")
    assert state["stage"] == flow.STAGE_ANSWER
    assert state["result"] is None  # typing never evaluates

    assert flow.submit_for_review(state) is True
    assert state["stage"] == flow.STAGE_REVIEW
    assert state["reviewed"] == "A collection of autonomous nodes."
    assert state["result"] is None  # reviewing never evaluates

    assert flow.confirm_evaluation(state, bank["ds-01"]) is True
    assert state["stage"] == flow.STAGE_EVALUATED
    assert state["result"]["question_id"] == "ds-01"
    assert flow.can_view_reference(state)


def test_editing_after_evaluation_invalidates_result(bank):
    state = flow.initial_state()
    flow.select_question(state, "ds-01")
    flow.update_draft(state, "A collection of autonomous nodes.")
    flow.submit_for_review(state)
    flow.confirm_evaluation(state, bank["ds-01"])
    assert flow.can_view_reference(state)

    flow.edit_after_evaluation(state)
    assert state["result"] is None
    assert state["stage"] == flow.STAGE_REVIEW
    assert not flow.can_view_reference(state)
    assert state["reviewed"] == "A collection of autonomous nodes."


def test_blank_draft_rejected_with_helpful_message():
    state = flow.initial_state()
    flow.select_question(state, "ds-15")
    flow.update_draft(state, "   \n  ")
    assert flow.submit_for_review(state) is False
    assert state["stage"] == flow.STAGE_ANSWER
    assert state["result"] is None
    assert "blank" in state["error"].lower()


def test_blank_reviewed_text_rejected_at_evaluation(bank):
    state = flow.initial_state()
    flow.select_question(state, "ds-15")
    flow.update_draft(state, "real text")
    flow.submit_for_review(state)
    flow.update_reviewed(state, "   ")
    assert flow.confirm_evaluation(state, bank["ds-15"]) is False
    assert state["stage"] == flow.STAGE_REVIEW
    assert state["result"] is None


def test_back_to_edit_keeps_text(bank):
    state = flow.initial_state()
    flow.select_question(state, "ds-15")
    flow.update_draft(state, "my explanation")
    flow.submit_for_review(state)
    flow.back_to_edit(state)
    assert state["stage"] == flow.STAGE_ANSWER
    assert state["draft"] == "my explanation"


def test_retry_clears_session_attempt(bank):
    state = flow.initial_state()
    flow.select_question(state, "ds-15")
    flow.update_draft(state, "some answer")
    flow.submit_for_review(state)
    flow.confirm_evaluation(state, bank["ds-15"])
    flow.retry_question(state)
    assert state["question_id"] == "ds-15"
    assert state["draft"] == state["reviewed"] == ""
    assert state["result"] is None
    assert state["stage"] == flow.STAGE_ANSWER


def test_evaluation_rejects_mismatched_question(bank):
    state = flow.initial_state()
    flow.select_question(state, "ds-15")
    flow.update_draft(state, "text")
    flow.submit_for_review(state)
    with pytest.raises(flow.FlowError, match="does not match"):
        flow.confirm_evaluation(state, bank["ds-08"])


def test_real_evaluator_integration_reports_coverage(bank):
    state = flow.initial_state()
    flow.select_question(state, "ds-15")
    flow.update_draft(
        state,
        "Since network splits will eventually happen, I must choose between "
        "consistency and availability.",
    )
    flow.submit_for_review(state)
    assert flow.confirm_evaluation(state, bank["ds-15"]) is True
    assert state["result"]["coverage_pct"] == 65.0
    assert state["result"]["earned_weight"] == 65.0
