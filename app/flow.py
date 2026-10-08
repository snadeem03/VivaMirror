"""Practice-flow state machine (US-01/US-02/US-05/US-09 slice).

Streamlit-independent and fully testable: explicit stages and transitions,
no widget calls, no persistence. Only current-session draft/review/result
data is stored here; nothing is written to disk.

Stages: "answer" -> "review" -> "evaluated".
"""

from __future__ import annotations

from app.evaluation import evaluate_answer

STAGE_ANSWER = "answer"
STAGE_REVIEW = "review"
STAGE_EVALUATED = "evaluated"

BLANK_MESSAGE = (
    "Write something first — a blank answer cannot be evaluated. "
    "Anything you already typed is kept, so just add your explanation "
    "and try again."
)


class FlowError(ValueError):
    """Raised for invalid flow operations (e.g. unknown question id)."""


def initial_state() -> dict:
    """Fresh flow state: no question selected, empty draft."""
    return {
        "question_id": None,
        "draft": "",
        "reviewed": "",
        "result": None,
        "stage": STAGE_ANSWER,
        "error": "",
    }


def select_question(state: dict, question_id: str) -> dict:
    """Select a question; resets its draft, reviewed answer, and result.

    Changing question never leaks a previous result into the new question.
    """
    if not isinstance(question_id, str) or not question_id.strip():
        raise FlowError("question_id must be a nonempty string")
    state["question_id"] = question_id
    state["draft"] = ""
    state["reviewed"] = ""
    state["result"] = None
    state["stage"] = STAGE_ANSWER
    state["error"] = ""
    return state


def update_draft(state: dict, text: str) -> dict:
    """Store draft text; typing never evaluates anything by itself."""
    state["draft"] = text if isinstance(text, str) else ""
    return state


def submit_for_review(state: dict) -> bool:
    """Move draft -> review. Rejects blank answers with a helpful message."""
    if not state["draft"].strip():
        state["error"] = BLANK_MESSAGE
        return False
    state["reviewed"] = state["draft"]
    state["stage"] = STAGE_REVIEW
    state["error"] = ""
    return True


def update_reviewed(state: dict, text: str) -> dict:
    """Store the edited review text; editing never evaluates by itself."""
    state["reviewed"] = text if isinstance(text, str) else ""
    return state


def back_to_edit(state: dict) -> dict:
    """Return to the answer stage, keeping the draft; drops any error."""
    state["draft"] = state["reviewed"] or state["draft"]
    state["stage"] = STAGE_ANSWER
    state["error"] = ""
    return state


def confirm_evaluation(state: dict, question: dict) -> bool:
    """Evaluate the reviewed text. Only this action produces a result."""
    if state["question_id"] is None or question is None:
        state["error"] = "Select a question before evaluating."
        return False
    if question.get("id") != state["question_id"]:
        raise FlowError("result question does not match the selected question")
    if not state["reviewed"].strip():
        state["error"] = BLANK_MESSAGE
        return False
    state["result"] = evaluate_answer(question, state["reviewed"])
    state["stage"] = STAGE_EVALUATED
    state["error"] = ""
    return True


def edit_after_evaluation(state: dict) -> dict:
    """Return an evaluated answer to review; invalidates the old result."""
    state["result"] = None
    state["stage"] = STAGE_REVIEW
    state["error"] = ""
    return state


def retry_question(state: dict) -> dict:
    """Start over on the same question (same-session practice, no history)."""
    state["draft"] = ""
    state["reviewed"] = ""
    state["result"] = None
    state["stage"] = STAGE_ANSWER
    state["error"] = ""
    return state


def can_view_reference(state: dict) -> bool:
    """The reference answer is visible only after a live evaluation."""
    return (
        state["stage"] == STAGE_EVALUATED
        and state["result"] is not None
        and state["result"].get("question_id") == state["question_id"]
    )
