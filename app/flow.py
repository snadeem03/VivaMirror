"""Practice-flow state machine (US-01/US-02/US-05/US-07/US-08/US-09 slice).

Streamlit-independent and fully testable: explicit stages and transitions,
no widget calls. Only current-session draft/review/result/save data is kept
in memory; persistence goes through :mod:`app.store` on explicit save only.
Raw audio is never part of this state (only transcript text).

Stages: "answer" -> "review" -> "evaluated".
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app import store
from app.evaluation import EVALUATOR_VERSION, evaluate_answer

STAGE_ANSWER = "answer"
STAGE_REVIEW = "review"
STAGE_EVALUATED = "evaluated"

MODE_TYPED = "typed"
MODE_SPOKEN = "spoken"
MODES = (MODE_TYPED, MODE_SPOKEN)

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
        "mode": MODE_TYPED,
        "draft": "",
        "audio": None,  # {"data": bytes, "mime": str, "name": str} | None
        "reviewed": "",
        "answer_source": "",  # "typed" | "spoken" | ""
        "result": None,
        "save_id": None,  # stable id for the current evaluation (idempotency)
        "saved": None,  # attempt id once this evaluation has been saved
        "assisted": False,  # reference revealed for this question (session)
        "show_reference": False,
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
    state["audio"] = None
    state["reviewed"] = ""
    state["answer_source"] = ""
    state["result"] = None
    state["save_id"] = None
    state["saved"] = None
    state["assisted"] = False
    state["show_reference"] = False
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
    state["answer_source"] = MODE_TYPED
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
    state["save_id"] = uuid.uuid4().hex  # new id per genuine evaluation
    state["saved"] = None
    state["stage"] = STAGE_EVALUATED
    state["error"] = ""
    return True


def edit_after_evaluation(state: dict) -> dict:
    """Return an evaluated answer to review; invalidates the old result."""
    state["result"] = None
    state["save_id"] = None
    state["saved"] = None
    state["stage"] = STAGE_REVIEW
    state["error"] = ""
    return state


def retry_question(state: dict) -> dict:
    """Start over on the same question (same-session practice, no history).

    Clears answer, audio, transcript, evaluation, and save identity — but
    keeps the session assistance flag: practice after a reveal stays
    assisted, and Try again must not launder it back to unassisted.
    """
    state["draft"] = ""
    state["audio"] = None
    state["reviewed"] = ""
    state["answer_source"] = ""
    state["result"] = None
    state["save_id"] = None
    state["saved"] = None
    state["stage"] = STAGE_ANSWER
    state["error"] = ""
    return state


def switch_mode(state: dict, mode: str) -> dict:
    """Switch typed/spoken input; clears result, keeps each mode's input."""
    if mode not in MODES:
        raise FlowError(f"mode must be one of {list(MODES)}, got {mode!r}")
    state["mode"] = mode
    state["reviewed"] = ""
    state["answer_source"] = ""
    state["result"] = None
    state["save_id"] = None
    state["saved"] = None
    state["stage"] = STAGE_ANSWER
    state["error"] = ""
    return state


def set_audio(state: dict, audio: dict | None) -> dict:
    """Store recorded/uploaded audio; new audio invalidates transcript/result."""
    if audio is not None:
        if (
            not isinstance(audio, dict)
            or not isinstance(audio.get("data"), (bytes, bytearray))
            or not audio["data"]
        ):
            raise FlowError("audio must be {'data': nonempty bytes, ...} or None")
    state["audio"] = (
        {"data": bytes(audio["data"]), "mime": audio.get("mime", ""),
         "name": audio.get("name", "")}
        if audio is not None
        else None
    )
    state["reviewed"] = ""
    state["answer_source"] = ""
    state["result"] = None
    state["stage"] = STAGE_ANSWER
    state["error"] = ""
    return state


def submit_transcript(state: dict, transcript: str) -> bool:
    """Move a fresh transcript -> review. Blank transcripts are rejected."""
    if not isinstance(transcript, str) or not transcript.strip():
        state["error"] = (
            "The transcription came back empty (silence or unintelligible "
            "audio). Re-record closer to the microphone, or type the answer "
            "instead — your audio is kept for another try."
        )
        return False
    state["reviewed"] = transcript
    state["answer_source"] = MODE_SPOKEN
    state["stage"] = STAGE_REVIEW
    state["error"] = ""
    return True


def reveal_reference(state: dict) -> dict:
    """Explicitly reveal the reference answer for this question (session).

    Marks subsequent practice on the question assisted. Cross-session
    assistance cannot be established, which the UI discloses.
    """
    state["assisted"] = True
    state["show_reference"] = True
    return state


def save_current(state: dict, question: dict, db_path=None) -> tuple[bool, dict]:
    """Save the current evaluation as one attempt (explicit save only).

    Uses the stable save_id minted at evaluation time, so reruns and double
    clicks return the stored row instead of duplicating it. A genuinely new
    evaluation carries a new save_id and creates a new row. Returns
    (inserted, stored_record); StoreError from the database propagates for
    the UI to report without losing reviewed text.
    """
    if state["stage"] != STAGE_EVALUATED or state["result"] is None:
        raise FlowError("nothing evaluated to save yet")
    if question is None or question.get("id") != state["question_id"]:
        raise FlowError("result question does not match the selected question")
    if not state.get("save_id"):
        raise FlowError("current evaluation has no save identity")
    record = {
        "id": state["save_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_id": state["question_id"],
        "rubric_fingerprint": store.fingerprint_for_question(question),
        "rubric_snapshot": store.snapshot_for_question(question),
        "evaluator_version": state["result"].get("evaluator_version")
        or EVALUATOR_VERSION,
        "input_mode": state["mode"],
        "reviewed_text": state["reviewed"],
        "result": state["result"],
        "coverage_pct": state["result"]["coverage_pct"],
        "assisted": bool(state.get("assisted", False)),
    }
    inserted, stored = store.save_attempt(db_path, record)
    if inserted:
        state["saved"] = stored["id"]
    return inserted, stored


def can_view_reference(state: dict) -> bool:
    """The reference answer is visible only after a live evaluation."""
    return (
        state["stage"] == STAGE_EVALUATED
        and state["result"] is not None
        and state["result"].get("question_id") == state["question_id"]
    )
