"""History, save, retry, and comparison UI tests (US-07/US-08 slice).

AppTest drives Practice → Save → History → Compare → Delete against a
temporary database selected via the VIVAMIRROR_DB environment variable —
the real local database is never touched. All answers are fictional
practice sentences, never student data.
"""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

MAIN = str(Path(__file__).resolve().parent.parent / "app" / "main.py")

THIN_DS15 = "Network splits will eventually happen."
FULL_DS15 = (
    "Since network splits will eventually happen, I must choose between "
    "consistency and availability; the trade-off applies during a partition. "
    "My CP design will refuse minority-side writes and reconcile divergent "
    "replicas afterwards, because without partitions all three hold and the "
    "pick-two slogan is misleading."
)


@pytest.fixture
def db(monkeypatch, tmp_path):
    path = str(tmp_path / "test-history.db")
    monkeypatch.setenv("VIVAMIRROR_DB", path)
    assert os.environ["VIVAMIRROR_DB"] == path
    return path


def _run():
    at = AppTest.from_file(MAIN)
    at.run()
    assert not at.exception, f"script raised: {at.exception}"
    return at


def _labels(at):
    return [option for option in at.selectbox(key="question_select").options]


def _practice_answer(at, text):
    at.text_area(key="draft_input").set_value(text).run()
    at.button(key="review_btn").click().run()
    at.button(key="evaluate_btn").click().run()
    assert not at.exception
    return at


def _save(at):
    at.button(key="save_btn").click().run()
    assert not at.exception
    return at


def _goto_history(at):
    at.sidebar.radio(key="nav").set_value("History").run()
    assert not at.exception
    return at


def _goto_practice(at):
    at.sidebar.radio(key="nav").set_value("Practice").run()
    assert not at.exception
    return at


def _headers(at):
    return [h.value for h in at.header]


# --- Save and history ---


def test_empty_history_state(db):
    at = _run()
    _goto_history(at)
    assert any("No saved attempts yet" in i.value for i in at.info)


def test_save_then_history_lists_attempt_with_progress(db):
    at = _run()
    at.selectbox(key="question_select").set_value(_labels(at)[14]).run()
    _practice_answer(at, THIN_DS15)
    assert "Concept coverage: 30.0%" in _headers(at)
    _save(at)
    assert any("Saved attempt" in s.value for s in at.success)

    _goto_history(at)
    assert any("1 saved attempt(s)" in m.value for m in at.markdown)
    assert any("best 30.0%" in m.value for m in at.markdown)
    assert any("latest 30.0%" in m.value for m in at.markdown)
    assert any("typed" in m.value and "unassisted" in m.value for m in at.markdown)


def test_double_save_does_not_duplicate(db):
    at = _run()
    at.selectbox(key="question_select").set_value(_labels(at)[14]).run()
    _practice_answer(at, THIN_DS15)
    _save(at)
    # After saving, the button is replaced by a confirmation; plain reruns
    # (the double-click path) must still create nothing new.
    at.run()
    at.run()
    _goto_history(at)
    assert any("1 saved attempt(s)" in m.value for m in at.markdown)


def test_retry_new_evaluation_saves_separate_row(db):
    at = _run()
    at.selectbox(key="question_select").set_value(_labels(at)[14]).run()
    _practice_answer(at, THIN_DS15)
    _save(at)
    at.button(key="retry_btn").click().run()
    _practice_answer(at, FULL_DS15)
    assert "Concept coverage: 100.0%" in _headers(at)
    _save(at)

    _goto_history(at)
    assert any("2 saved attempt(s)" in m.value for m in at.markdown)
    assert any("best 100.0%" in m.value for m in at.markdown)
    assert any("latest 100.0%" in m.value for m in at.markdown)


# --- Comparison ---


def _save_two_attempts(at):
    at.selectbox(key="question_select").set_value(_labels(at)[14]).run()
    _practice_answer(at, THIN_DS15)
    _save(at)
    at.button(key="retry_btn").click().run()
    _practice_answer(at, FULL_DS15)
    _save(at)
    _goto_history(at)
    return at


def test_compare_shows_percentage_point_delta_and_newly_covered(db):
    at = _save_two_attempts(_run())
    at.button(key="compare_btn").click().run()
    assert not at.exception
    assert any("+70.0 percentage points" in h for h in _headers(at))
    assert any("does not prove improved correctness" in m.value for m in at.markdown)
    assert any("Newly covered" in s.value for s in at.subheader)
    assert any("CP versus AP behaviour" in m.value for m in at.markdown)


def test_weaker_later_attempt_reports_negative_delta_and_regression(db):
    # Comparison is chronological: a weaker LATER attempt yields a negative
    # delta and a regressed list (selection order never inverts time).
    at = _run()
    at.selectbox(key="question_select").set_value(_labels(at)[14]).run()
    _practice_answer(at, FULL_DS15)
    _save(at)
    at.button(key="retry_btn").click().run()
    _practice_answer(at, THIN_DS15)
    _save(at)

    _goto_history(at)
    at.button(key="compare_btn").click().run()
    assert any("-70.0 percentage points" in h for h in _headers(at))
    assert any("No longer detected" in s.value for s in at.subheader)
    assert any("CP versus AP behaviour" in m.value for m in at.markdown)


# --- Assistance ---


def test_reveal_marks_save_assisted_and_retry_keeps_it(db):
    at = _run()
    at.selectbox(key="question_select").set_value(_labels(at)[14]).run()
    _practice_answer(at, THIN_DS15)
    at.button(key="reveal_btn").click().run()
    _save(at)
    at.button(key="retry_btn").click().run()  # must not launder assistance
    _practice_answer(at, FULL_DS15)
    _save(at)

    _goto_history(at)
    badges = [m.value for m in at.markdown]
    assert sum("assisted" in b for b in badges) >= 2


def test_unassisted_save_labeled_honestly(db):
    at = _run()
    at.selectbox(key="question_select").set_value(_labels(at)[14]).run()
    _practice_answer(at, THIN_DS15)
    _save(at)
    _goto_history(at)
    assert any("unassisted" in m.value for m in at.markdown)


# --- Deletion ---


def test_delete_one_attempt(db):
    at = _save_two_attempts(_run())
    options = list(at.selectbox(key="del_one").options)
    assert len(options) == 2
    at.selectbox(key="del_one").set_value(options[0]).run()
    at.button(key="del_btn").click().run()
    assert any("Deleted." in s.value for s in at.success)
    assert any("1 saved attempt(s)" in m.value for m in at.markdown)


def test_delete_all_requires_explicit_confirmation(db):
    from streamlit.testing.v1.errors import AppTestError

    at = _save_two_attempts(_run())
    assert at.button(key="wipe_btn").disabled is True
    with pytest.raises(AppTestError):  # a browser user cannot click it either
        at.button(key="wipe_btn").click().run()
    assert any("2 saved attempt(s)" in m.value for m in at.markdown)
    at.checkbox(key="confirm_wipe").set_value(True).run()
    at.button(key="wipe_btn").click().run()
    assert any("Deleted 2 attempt(s)." in s.value for s in at.success)
    assert any("No saved attempts yet" in i.value for i in at.info)


# --- Failure and isolation ---


def test_failed_save_keeps_reviewed_answer(monkeypatch, tmp_path):
    monkeypatch.setenv("VIVAMIRROR_DB", str(tmp_path))  # a directory, not a file
    at = _run()
    at.selectbox(key="question_select").set_value(_labels(at)[14]).run()
    _practice_answer(at, THIN_DS15)
    at.button(key="save_btn").click().run()
    assert at.warning, "expected a save-failure message"
    assert "kept" in at.warning[0].value.lower()
    assert "Concept coverage: 30.0%" in _headers(at)  # result intact
    at.button(key="edit_btn").click().run()  # reviewed text survived
    assert at.text_area(key="review_input").value == THIN_DS15


def test_history_never_overwrites_current_draft(db):
    at = _run()
    at.selectbox(key="question_select").set_value(_labels(at)[14]).run()
    _practice_answer(at, THIN_DS15)
    _save(at)
    at.button(key="retry_btn").click().run()
    at.text_area(key="draft_input").set_value("work in progress").run()
    _goto_history(at)
    at.button(key="compare_btn").click().run()
    _goto_practice(at)
    assert at.text_area(key="draft_input").value == "work in progress"
