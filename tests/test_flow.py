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


# --- Spoken-mode state (US-03/US-04 slice) ---


def _audio(n=10):
    return {"data": bytes(range(n)), "mime": "audio/wav", "name": "answer.wav"}


def test_select_question_clears_audio_and_source(bank):
    state = flow.initial_state()
    flow.select_question(state, "ds-15")
    flow.switch_mode(state, flow.MODE_SPOKEN)
    flow.set_audio(state, _audio())
    flow.submit_transcript(state, "some transcript")
    assert state["answer_source"] == flow.MODE_SPOKEN

    flow.select_question(state, "ds-08")
    assert state["audio"] is None
    assert state["reviewed"] == ""
    assert state["answer_source"] == ""
    assert state["result"] is None
    assert state["mode"] == flow.MODE_SPOKEN  # input preference is kept


def test_switch_mode_preserves_inputs_but_clears_result(bank):
    state = flow.initial_state()
    flow.select_question(state, "ds-15")
    flow.update_draft(state, "typed words")
    flow.switch_mode(state, flow.MODE_SPOKEN)
    flow.set_audio(state, _audio())
    flow.submit_transcript(state, "spoken transcript")
    flow.confirm_evaluation(state, bank["ds-15"])
    assert flow.can_view_reference(state)

    flow.switch_mode(state, flow.MODE_TYPED)
    assert state["result"] is None
    assert state["reviewed"] == ""
    assert not flow.can_view_reference(state)
    assert state["draft"] == "typed words"  # typed input not lost
    assert state["audio"] is not None  # recording not lost either
    assert state["stage"] == flow.STAGE_ANSWER


def test_switch_mode_rejects_unknown_mode():
    with pytest.raises(flow.FlowError, match="mode"):
        flow.switch_mode(flow.initial_state(), "telepathy")


def test_set_audio_requires_real_bytes():
    state = flow.initial_state()
    with pytest.raises(flow.FlowError):
        flow.set_audio(state, {"data": b"", "mime": "", "name": ""})
    with pytest.raises(flow.FlowError):
        flow.set_audio(state, "nope")
    assert flow.set_audio(state, None)["audio"] is None


def test_submit_transcript_enters_review_without_evaluating(bank):
    state = flow.initial_state()
    flow.select_question(state, "ds-10")
    flow.switch_mode(state, flow.MODE_SPOKEN)
    assert flow.submit_transcript(state, "   ") is False
    assert state["stage"] == flow.STAGE_ANSWER
    assert "empty" in state["error"].lower()

    assert flow.submit_transcript(state, "spoken words here") is True
    assert state["stage"] == flow.STAGE_REVIEW
    assert state["answer_source"] == flow.MODE_SPOKEN
    assert state["result"] is None  # transcription never auto-evaluates


def test_retry_clears_audio(bank):
    state = flow.initial_state()
    flow.select_question(state, "ds-15")
    flow.switch_mode(state, flow.MODE_SPOKEN)
    flow.set_audio(state, _audio())
    flow.retry_question(state)
    assert state["audio"] is None
    assert state["answer_source"] == ""


# --- Explicit save and assistance (US-07/US-08 slice) ---


def _evaluated(bank, qid="ds-15", text="Network splits will eventually happen."):
    state = flow.initial_state()
    flow.select_question(state, qid)
    flow.update_draft(state, text)
    flow.submit_for_review(state)
    assert flow.confirm_evaluation(state, bank[qid]) is True
    return state


def test_save_current_round_trip_and_idempotent_resave(bank, tmp_path):
    from app import store as store_module

    db = str(tmp_path / "t.db")
    state = _evaluated(bank)
    assert state["save_id"]
    inserted, stored = flow.save_current(state, bank["ds-15"], db)
    assert inserted is True
    assert state["saved"] == stored["id"] == state["save_id"]
    assert stored["reviewed_text"].startswith("Network splits")
    assert stored["input_mode"] == "typed"
    assert stored["assisted"] is False

    inserted, stored = flow.save_current(state, bank["ds-15"], db)
    assert inserted is False  # rerun/double-click duplicates nothing
    assert len(store_module.list_attempts(db)) == 1


def test_new_evaluation_gets_new_save_identity(bank, tmp_path):
    from app import store as store_module

    db = str(tmp_path / "t.db")
    first = _evaluated(bank)
    _, stored_first = flow.save_current(first, bank["ds-15"], db)
    flow.retry_question(first)
    assert first["saved"] is None  # save identity cleared with the attempt
    flow.update_draft(first, "Without partitions all three hold.")
    flow.submit_for_review(first)
    flow.confirm_evaluation(first, bank["ds-15"])
    assert first["save_id"]  # a genuinely new evaluation mints a new id
    _, stored_second = flow.save_current(first, bank["ds-15"], db)
    assert stored_second["id"] != stored_first["id"]
    assert len(store_module.list_attempts(db)) == 2


def test_save_requires_an_evaluation(bank, tmp_path):
    state = flow.initial_state()
    flow.select_question(state, "ds-15")
    with pytest.raises(flow.FlowError, match="nothing evaluated"):
        flow.save_current(state, bank["ds-15"], str(tmp_path / "t.db"))


def test_retry_preserves_assistance_but_select_resets(bank):
    state = flow.initial_state()
    flow.select_question(state, "ds-15")
    assert state["assisted"] is False
    flow.reveal_reference(state)
    assert state["assisted"] is True
    assert state["show_reference"] is True
    flow.retry_question(state)  # Try again must not launder assistance
    assert state["assisted"] is True
    assert state["show_reference"] is True
    flow.select_question(state, "ds-08")  # new question, fresh session flag
    assert state["assisted"] is False
    assert state["show_reference"] is False


def test_edit_and_mode_switch_clear_save_identity(bank):
    state = _evaluated(bank)
    assert state["save_id"]
    flow.edit_after_evaluation(state)
    assert state["save_id"] is None
    assert state["saved"] is None

    state = _evaluated(bank)
    flow.switch_mode(state, flow.MODE_SPOKEN)
    assert state["save_id"] is None


def test_spoken_save_records_input_mode(bank, tmp_path):
    state = flow.initial_state()
    flow.select_question(state, "ds-15")
    flow.switch_mode(state, flow.MODE_SPOKEN)
    flow.set_audio(state, _audio())
    flow.submit_transcript(state, "Network splits will eventually happen.")
    flow.confirm_evaluation(state, bank["ds-15"])
    _, stored = flow.save_current(state, bank["ds-15"], str(tmp_path / "t.db"))
    assert stored["input_mode"] == "spoken"
