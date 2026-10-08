"""UI behavior tests for the typed-answer practice flow (US-01/US-02/US-05).

Uses Streamlit AppTest to drive the real interface: selecting questions,
typing, reviewing, evaluating, and reading rendered output. Pure state
behavior is covered separately in tests/test_flow.py.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

MAIN = str(Path(__file__).resolve().parent.parent / "app" / "main.py")

PARTIAL_DS15 = (
    "Since network splits will eventually happen, I must choose between "
    "consistency and availability."
)


def _run():
    at = AppTest.from_file(MAIN)
    at.run()
    assert not at.exception, f"script raised: {at.exception}"
    return at


def _labels(at):
    return [option for option in at.selectbox(key="question_select").options]


def _headers(at):
    return [h.value for h in at.header]


def _select_question(at, idx):
    """Select a bank question by index (tests use ds-15 content: idx 14)."""
    at.selectbox(key="question_select").set_value(_labels(at)[idx]).run()
    assert not at.exception
    return at


def test_initial_load_lists_all_15_questions():
    at = _run()
    assert len(_labels(at)) == 15
    assert "CAP theorem" in _labels(at)[-1]
    assert at.text_area(key="draft_input") is not None
    assert at.expander == []  # no reference before evaluation


def test_question_change_resets_stale_result():
    at = _run()
    _select_question(at, 14)
    at.text_area(key="draft_input").set_value(PARTIAL_DS15).run()
    at.button(key="review_btn").click().run()
    at.button(key="evaluate_btn").click().run()
    assert "Concept coverage: 65.0%" in _headers(at)

    _select_question(at, 7)
    assert not any("Concept coverage" in h for h in _headers(at))
    assert at.text_area(key="draft_input").value == ""
    assert at.expander == []


def test_draft_review_evaluate_flow_reports_real_coverage():
    at = _run()
    _select_question(at, 14)
    at.text_area(key="draft_input").set_value(PARTIAL_DS15).run()
    assert not any("Concept coverage" in h for h in _headers(at))

    at.button(key="review_btn").click().run()
    assert not any("Concept coverage" in h for h in _headers(at))
    assert PARTIAL_DS15 in [t.value for t in at.text]

    at.button(key="evaluate_btn").click().run()
    assert "Concept coverage: 65.0%" in _headers(at)
    assert len(at.expander) == 1  # reference available only after evaluation


def test_blank_answer_rejected_with_message():
    at = _run()
    at.button(key="review_btn").click().run()
    assert not any("Concept coverage" in h for h in _headers(at))
    assert at.warning, "expected a helpful blank-submission message"
    assert "blank" in at.warning[0].value.lower()


def test_edit_after_evaluation_invalidates_result():
    at = _run()
    _select_question(at, 14)
    at.text_area(key="draft_input").set_value(PARTIAL_DS15).run()
    at.button(key="review_btn").click().run()
    at.button(key="evaluate_btn").click().run()
    assert "Concept coverage: 65.0%" in _headers(at)

    at.button(key="edit_btn").click().run()
    assert not any("Concept coverage" in h for h in _headers(at))
    assert at.expander == []  # reference hidden again once editing resumes
    assert PARTIAL_DS15 in at.text_area(key="review_input").value


def test_rerun_without_input_keeps_result():
    at = _run()
    _select_question(at, 14)
    at.text_area(key="draft_input").set_value(PARTIAL_DS15).run()
    at.button(key="review_btn").click().run()
    at.button(key="evaluate_btn").click().run()
    at.run()  # plain rerun: must not re-evaluate or wipe anything
    assert not at.exception
    assert "Concept coverage: 65.0%" in _headers(at)


def test_unsafe_answer_text_rendered_as_plain_text():
    payload = "<script>alert('xss')</script><b>bold?</b>"
    at = _run()
    at.text_area(key="draft_input").set_value(payload).run()
    at.button(key="review_btn").click().run()
    assert not at.exception
    # Student content surfaces only through st.text (plain-text elements):
    # the raw payload is visible as text and never reaches markdown/HTML.
    assert payload in [t.value for t in at.text]
    assert all(payload not in m.value for m in at.markdown)
    at.button(key="evaluate_btn").click().run()
    assert not at.exception
    # Feedback shows no evidence spans for unmatched text, but the payload
    # must still never reach markdown/HTML rendering paths.
    assert any("Concept coverage" in h for h in _headers(at))
    assert all(payload not in m.value for m in at.markdown)


def test_try_again_starts_fresh_attempt():
    at = _run()
    _select_question(at, 14)
    at.text_area(key="draft_input").set_value(PARTIAL_DS15).run()
    at.button(key="review_btn").click().run()
    at.button(key="evaluate_btn").click().run()
    assert "Concept coverage: 65.0%" in _headers(at)

    at.button(key="retry_btn").click().run()
    assert not any("Concept coverage" in h for h in _headers(at))
    assert at.text_area(key="draft_input").value == ""
    assert at.expander == []


@pytest.mark.parametrize("idx", [0, 7, 14])
def test_every_question_renders_its_prompt(idx):
    from app.questions import load_question_bank

    bank = load_question_bank()
    at = _run()
    at.selectbox(key="question_select").set_value(_labels(at)[idx]).run()
    assert not at.exception
    assert bank[idx]["question_text"] in [t.value for t in at.text] + [
        m.value for m in at.markdown
    ]
