"""VivaMirror Streamlit entry point — typed and spoken practice flow.

Launch from the repository root with the Python 3.11 environment::

    .\\.venv\\Scripts\\python.exe -m streamlit run app/main.py

Typed practice always works. Spoken answers need the optional audio stack
(``pip install -r requirements-audio.txt``); without it the UI says so and
typed practice is unaffected. No persistence, no login, no external
services. UI state lives in ``st.session_state`` for the current session;
transitions are owned by :mod:`app.flow` so reruns can never transcribe,
evaluate, or overwrite input by themselves.
"""

from __future__ import annotations

import streamlit as st

from app import flow
from app.questions import load_question_bank
from app.transcribe import (
    FasterWhisperBackend,
    TranscriptionError,
    speech_stack_available,
    transcribe_audio,
)

MODE_LABELS = {"typed": "Typed answer", "spoken": "Spoken answer"}

STATUS_ORDER = ("covered", "needs_review", "not_detected")
STATUS_HEADING = {
    "covered": "Covered",
    "needs_review": "Needs review",
    "not_detected": "Not detected",
}


@st.cache_data
def get_bank() -> list[dict]:
    """Load the validated question bank once per session."""
    return load_question_bank()


def _state() -> dict:
    if "vm" not in st.session_state:
        st.session_state.vm = flow.initial_state()
    return st.session_state.vm


def _get_transcriber():
    """Production backend, unless a test double was injected.

    Tests may set ``st.session_state["vm_transcriber"]`` to a fake object
    with ``transcribe(path) -> (text, language)``. That double is clearly
    labeled in the test files and is never a production fallback.
    """
    injected = st.session_state.get("vm_transcriber")
    if injected is not None:
        return injected
    return FasterWhisperBackend()


def _read_upload(uploaded) -> dict:
    """Normalize a mic/upload UploadedFile to raw bytes plus metadata."""
    return {
        "data": bytes(uploaded.getvalue()),
        "mime": uploaded.type or "",
        "name": uploaded.name or "answer.wav",
    }


def _answer_audio() -> dict | None:
    """Currently available spoken input, without transcribing anything.

    Microphone recording wins over an uploaded file when both exist.
    """
    mic = st.session_state.get("mic_input")
    if mic is not None:
        return _read_upload(mic)
    upload = st.session_state.get("upload_input")
    if upload is not None:
        return _read_upload(upload)
    return None


def _find_question(bank: list[dict], question_id: str) -> dict | None:
    for question in bank:
        if question["id"] == question_id:
            return question
    return None


def _render_feedback(vm: dict) -> None:
    result = vm["result"]
    st.header(f"Concept coverage: {result['coverage_pct']}%")
    st.write(
        "This percentage counts rubric weight with matched phrase evidence "
        f"({result['earned_weight']:g} of {result['available_weight']:g}). "
        "It is **not a correctness grade** — a matched phrase is evidence, "
        "not proof that the explanation is right."
    )
    groups: dict[str, list[dict]] = {status: [] for status in STATUS_ORDER}
    for concept in result["concepts"]:
        groups[concept["status"]].append(concept)
    if groups["needs_review"]:
        st.warning(
            "Conflicting evidence was found for at least one concept "
            "(shown below). Those concepts earn zero weight until a human "
            "judges which reading holds."
        )
    for status in STATUS_ORDER:
        if not groups[status]:
            continue
        st.subheader(STATUS_HEADING[status])
        for concept in groups[status]:
            st.markdown(
                f"**{concept['label']}** — "
                f"earned {concept['earned_weight']:g} of {concept['weight']:g}"
            )
            st.write(concept["explanation"])
            if status == "not_detected" and not concept["conflicting_evidence"]:
                st.write(
                    "No evidence was detected. This does not mean you are "
                    "wrong or do not know the concept."
                )
            for span in concept["evidence"]:
                st.text(f"Evidence: {span['text']}")
            for span in concept["conflicting_evidence"]:
                # Plain text only: student content is never rendered as HTML.
                st.text(f"Conflicting: {span['text']}")


def main() -> None:
    st.set_page_config(page_title="VivaMirror — Practice Viva", layout="centered")
    st.title("VivaMirror — Practice Viva")
    st.info(
        "Typed practice always works. Spoken answers need the optional "
        "audio stack; without it the app says so and typed practice is "
        "unaffected. Nothing you enter or record is saved anywhere."
    )

    try:
        bank = get_bank()
    except Exception as exc:  # FileNotFoundError / validation errors
        st.error(f"Could not load the curated question bank: {exc}")
        st.stop()

    vm = _state()
    if vm["question_id"] is None:
        flow.select_question(vm, bank[0]["id"])

    labels = [f"{q['topic']} — {q['difficulty']}" for q in bank]
    ids = [q["id"] for q in bank]
    current_index = ids.index(vm["question_id"]) if vm["question_id"] in ids else 0
    choice = st.selectbox(
        "Distributed Systems question (15 curated)",
        labels,
        index=current_index,
        key="question_select",
    )
    chosen_id = ids[labels.index(choice)]
    if chosen_id != vm["question_id"]:
        flow.select_question(vm, chosen_id)
        for key in ("draft_input", "review_input", "mic_input", "upload_input"):
            st.session_state.pop(key, None)
        st.rerun()

    question = _find_question(bank, vm["question_id"])
    if question is None:  # Bank changed under a live session; recover cleanly.
        flow.select_question(vm, bank[0]["id"])
        st.rerun()
        return

    st.subheader("Question")
    st.write(question["question_text"])
    mode_label = (
        "spoken answer (transcribed)"
        if vm.get("answer_source") == flow.MODE_SPOKEN
        else "typed answer"
    )
    st.caption(
        f"ID {question['id']} · difficulty {question['difficulty']} · "
        f"{mode_label} — say so in your demo"
    )

    mode_choice = st.radio(
        "Answer mode",
        [MODE_LABELS["typed"], MODE_LABELS["spoken"]],
        index=0 if vm.get("mode", flow.MODE_TYPED) == flow.MODE_TYPED else 1,
        key="mode_radio",
        horizontal=True,
    )
    want_mode = (
        flow.MODE_SPOKEN if mode_choice == MODE_LABELS["spoken"] else flow.MODE_TYPED
    )
    if want_mode != vm.get("mode", flow.MODE_TYPED):
        # Persist whatever text is on screen first, so switching modes never
        # silently drops words; the stale result/review is still invalidated.
        latest = st.session_state.get(
            "review_input", st.session_state.get("draft_input", vm["draft"])
        )
        flow.update_draft(vm, latest if isinstance(latest, str) else "")
        flow.switch_mode(vm, want_mode)
        st.session_state.pop("review_input", None)
        st.rerun()

    if vm["stage"] == flow.STAGE_ANSWER and vm.get("mode") == flow.MODE_SPOKEN:
        st.subheader("Your answer (spoken)")
        st.write(
            "Record with the microphone (the browser asks for permission; "
            "recording works on localhost and HTTPS) or upload a short clip. "
            "Play it back, then press **Transcribe** — transcription only "
            "ever runs when you press that button."
        )
        if st.session_state.get("vm_transcriber") is None and not speech_stack_available():
            st.warning(
                "Audio support is not installed in this environment "
                "(faster-whisper missing). You can still record or upload, "
                "but Transcribe will report the missing dependency — or just "
                "use Typed answer instead. Install it with: "
                "`pip install -r requirements-audio.txt`"
            )
        st.audio_input("Record your answer", key="mic_input")
        st.file_uploader(
            "Or upload an audio file (wav, mp3, m4a, ogg, flac, webm)",
            type=["wav", "mp3", "m4a", "ogg", "flac", "webm"],
            key="upload_input",
        )
        source = _answer_audio()
        if source is None:
            st.write("No audio yet — record or upload a clip to enable transcription.")
        else:
            st.audio(source["data"], format=source.get("mime") or None)
            st.caption(
                f"{source.get('name', 'recording')} · "
                f"{len(source['data']) / 1024:.0f} KB · "
                "limits: 20 MB and 3 minutes"
            )
            if st.button("Transcribe", key="transcribe_btn"):
                flow.set_audio(vm, source)
                try:
                    with st.spinner(
                        "Transcribing locally — the first run downloads the "
                        "speech model (~150 MB) and needs internet once."
                    ):
                        outcome = transcribe_audio(
                            source["data"],
                            source.get("name") or "answer.wav",
                            transcriber=_get_transcriber(),
                        )
                except TranscriptionError as exc:
                    vm["error"] = f"{exc} You can also type the answer instead."
                else:
                    if flow.submit_transcript(vm, outcome["transcript"]):
                        st.session_state.review_input = vm["reviewed"]
                        st.rerun()
            if vm["error"]:
                st.warning(vm["error"])
        st.caption(
            "Privacy: audio stays in this browser session for playback until "
            "you replace it, change question, or close the page. VivaMirror "
            "never uploads it anywhere and never saves it; transcription "
            "stages it through a short-lived temp file that is deleted "
            "immediately after."
        )

    elif vm["stage"] == flow.STAGE_ANSWER:
        st.subheader("Your answer (typed)")
        st.write(
            "Explain in your own words, as if speaking in the viva. "
            "Write a few sentences first — you will review and edit "
            "before anything is evaluated. No example wording is shown "
            "on purpose."
        )
        if "draft_input" not in st.session_state:
            st.session_state.draft_input = vm["draft"]
        st.text_area("Type your answer here", height=180, key="draft_input")
        if st.button("Review answer", key="review_btn"):
            flow.update_draft(vm, st.session_state.draft_input)
            if flow.submit_for_review(vm):
                st.session_state.review_input = vm["reviewed"]
                st.rerun()
        if vm["error"]:
            st.warning(vm["error"])

    elif vm["stage"] == flow.STAGE_REVIEW:
        st.subheader("Review your answer")
        if vm.get("answer_source") == flow.MODE_SPOKEN:
            st.caption(
                "Source: transcribed speech — transcription is approximate; "
                "correct any misheard words before evaluating. Transcription "
                "accuracy and concept coverage are separate things."
            )
        st.write("This exact text will be evaluated. Edit it first if needed:")
        st.text(vm["reviewed"])
        st.text_area("Edit your answer", height=180, key="review_input")
        left, right = st.columns(2)
        if left.button("Evaluate reviewed answer", key="evaluate_btn"):
            flow.update_reviewed(vm, st.session_state.review_input)
            if flow.confirm_evaluation(vm, question):
                st.rerun()
        if right.button("Back to edit", key="back_btn"):
            flow.back_to_edit(vm)
            st.session_state.draft_input = vm["draft"]
            st.rerun()
        if vm["error"]:
            st.warning(vm["error"])

    elif vm["stage"] == flow.STAGE_EVALUATED:
        if not flow.can_view_reference(vm):
            # A stale result must never leak into the current view.
            flow.retry_question(vm)
            for key in ("draft_input", "review_input", "mic_input", "upload_input"):
                st.session_state.pop(key, None)
            st.rerun()
            return
        st.subheader("Feedback")
        _render_feedback(vm)
        with st.expander("Reference answer (reveals the rubric wording)"):
            st.write(question["reference_answer"])
            st.write(
                "Reading this makes further practice on this question "
                "**assisted**: it is still useful for learning, but do not "
                "present a later attempt as an unseen assessment."
            )
            st.write(f"Follow-up to try next: {question['follow_up']}")
        left, right = st.columns(2)
        if left.button("Edit answer", key="edit_btn"):
            flow.edit_after_evaluation(vm)
            st.session_state.review_input = vm["reviewed"]
            st.rerun()
        if right.button("Try again", key="retry_btn"):
            flow.retry_question(vm)
            for key in ("draft_input", "review_input", "mic_input", "upload_input"):
                st.session_state.pop(key, None)
            st.rerun()


if __name__ == "__main__":
    main()
