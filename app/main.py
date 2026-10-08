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

import os

import streamlit as st

from app import flow, store
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


def _db_path() -> str:
    """Local history database path.

    ``VIVAMIRROR_DB`` overrides it (used by tests for temp databases);
    otherwise the ignored local runtime path under ``data/local/``.
    """
    override = os.environ.get("VIVAMIRROR_DB")
    return override if override else str(store.default_db_path())


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


def _attempt_label(attempt: dict) -> str:
    tag = "assisted" if attempt["assisted"] else "unassisted"
    created = attempt["created_at"].replace("T", " ")[:16]
    return (
        f"{created} · {attempt['coverage_pct']:.1f}% · "
        f"{attempt['input_mode']} · {tag} · {attempt['id'][:8]}"
    )


def _render_history(bank: list[dict]) -> None:
    st.header("History")
    st.caption(
        "Saved attempts live in a local database on this computer only — "
        "one shared installation history, no accounts, no user separation."
    )
    message = st.session_state.pop("hist_msg", "")
    if message:
        st.success(message)
    try:
        attempts = store.list_attempts(_db_path())
    except store.StoreError as exc:
        st.error(f"Could not read the local history ({exc}).")
        return
    if not attempts:
        st.info(
            "No saved attempts yet. Evaluate an answer in Practice, then "
            "press **Save attempt** — only explicitly saved attempts appear "
            "here."
        )
        return

    by_question: dict[str, list[dict]] = {}
    for attempt in attempts:
        by_question.setdefault(attempt["question_id"], []).append(attempt)
    labels = []
    ids = []
    for question in bank:
        if question["id"] in by_question:
            count = len(by_question[question["id"]])
            labels.append(f"{question['topic']} ({count} saved)")
            ids.append(question["id"])
    chosen = st.selectbox("Question history", labels, key="hist_question")
    qid = ids[labels.index(chosen)]
    mine = by_question[qid]
    coverages = [a["coverage_pct"] for a in mine]
    st.write(
        f"{len(mine)} saved attempt(s) · best {max(coverages):.1f}% · "
        f"latest {coverages[-1]:.1f}%"
    )

    options = [_attempt_label(a) for a in mine]
    by_label = dict(zip(options, mine))
    default_b = len(options) - 1
    default_a = max(0, default_b - 1)
    label_a = st.selectbox("Earlier attempt", options, index=default_a, key="cmp_a")
    label_b = st.selectbox("Later attempt", options, index=default_b, key="cmp_b")
    if st.button("Compare", key="compare_btn"):
        st.session_state["compare_pair"] = (
            by_label[label_a]["id"],
            by_label[label_b]["id"],
        )
    pair = st.session_state.get("compare_pair")
    if pair is not None:
        first = next((a for a in mine if a["id"] == pair[0]), None)
        second = next((a for a in mine if a["id"] == pair[1]), None)
        if first is None or second is None:
            st.warning("One of the selected attempts no longer exists.")
        else:
            _render_comparison(first, second)

    st.subheader("Saved answers")
    for attempt in reversed(mine):
        assisted = "assisted" if attempt["assisted"] else "unassisted"
        st.markdown(
            f"**{_attempt_label(attempt)}** — "
            f"{attempt['coverage_pct']:.1f}% ({assisted})"
        )
        st.text(attempt["reviewed_text"])

    st.subheader("Delete")
    del_options = [_attempt_label(a) for a in attempts]
    st.selectbox("Attempt to delete", del_options, key="del_one")

    def _do_delete_one() -> None:
        label = st.session_state.get("del_one", "")
        target = next(
            (a for a in attempts if _attempt_label(a) == label), None
        )
        if target is None:
            st.session_state["hist_msg"] = "That attempt is already gone."
            return
        try:
            removed = store.delete_attempt(_db_path(), target["id"])
        except store.StoreError as exc:
            st.session_state["hist_msg"] = f"Could not delete ({exc})."
        else:
            st.session_state.pop("compare_pair", None)
            st.session_state["hist_msg"] = (
                "Deleted." if removed else "Already gone."
            )

    def _do_wipe_all() -> None:
        try:
            count = store.delete_all_attempts(_db_path())
        except store.StoreError as exc:
            st.session_state["hist_msg"] = f"Could not delete ({exc})."
        else:
            st.session_state.pop("compare_pair", None)
            st.session_state["hist_msg"] = f"Deleted {count} attempt(s)."
        st.session_state["confirm_wipe"] = False

    st.button("Delete selected attempt", key="del_btn", on_click=_do_delete_one)
    st.checkbox(
        f"Yes, delete all {len(attempts)} saved attempt(s)",
        key="confirm_wipe",
    )
    st.button(
        "Delete all attempts",
        key="wipe_btn",
        disabled=not st.session_state.get("confirm_wipe", False),
        on_click=_do_wipe_all,
    )


def _render_comparison(first: dict, second: dict) -> None:
    st.subheader("Comparison")
    earlier, later = (
        (first, second)
        if (first["created_at"], first["id"]) <= (second["created_at"], second["id"])
        else (second, first)
    )
    try:
        result = store.compare_attempts(earlier, later)
    except store.StoreError as exc:
        st.error(f"Could not compare ({exc}).")
        return
    st.write(
        f"Earlier: {result['earlier']['created_at'].replace('T', ' ')[:16]} · "
        f"{result['earlier']['coverage_pct']:.1f}% · "
        f"{result['earlier']['input_mode']} · "
        f"{'assisted' if result['earlier']['assisted'] else 'unassisted'}"
    )
    st.write(
        f"Later: {result['later']['created_at'].replace('T', ' ')[:16]} · "
        f"{result['later']['coverage_pct']:.1f}% · "
        f"{result['later']['input_mode']} · "
        f"{'assisted' if result['later']['assisted'] else 'unassisted'}"
    )
    if not result["comparable"]:
        st.warning(result["reason"])
        return
    delta = result["coverage_delta_pp"]
    st.header(f"{delta:+.1f} percentage points")
    st.write(
        "Percentage points, not percent improvement — and a higher value "
        "does not prove improved correctness or speaking ability."
    )
    if result["newly_covered"]:
        st.subheader("Newly covered")
        for item in result["newly_covered"]:
            st.write(f"+ {item['label']}")
    if result["regressed"]:
        st.subheader("No longer detected / needs review")
        for item in result["regressed"]:
            st.write(f"− {item['label']} (now: {item['later_status']})")
    if not result["newly_covered"] and not result["regressed"]:
        st.write("No per-concept changes between these attempts.")
    st.caption("Reviewed answers under inspection:")
    st.text(f"Earlier: {earlier['reviewed_text']}")
    st.text(f"Later: {later['reviewed_text']}")


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

    nav = st.sidebar.radio("Navigate", ["Practice", "History"], key="nav")
    if nav == "History":
        # History is read-only: persist on-screen text into session state
        # first so the round trip can never wipe a draft or review edit.
        if "draft_input" in st.session_state:
            flow.update_draft(vm, st.session_state.draft_input)
        if "review_input" in st.session_state:
            flow.update_reviewed(vm, st.session_state.review_input)
        _render_history(bank)
        return

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
        custom_transcriber = st.session_state.get("vm_transcriber") is not None
        if not custom_transcriber and not speech_stack_available():
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
        if "review_input" not in st.session_state:
            st.session_state.review_input = vm["reviewed"]
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

        if vm.get("saved"):
            st.success(
                f"Saved attempt {vm['saved'][:8]}… — stored locally on this "
                "computer only. Saving again will not duplicate it."
            )
        elif st.button("Save attempt", key="save_btn"):
            try:
                inserted, stored = flow.save_current(vm, question, _db_path())
            except store.StoreError as exc:
                # The reviewed answer is untouched: nothing is lost.
                vm["error"] = (
                    f"Could not save this attempt ({exc}). Your reviewed "
                    "answer is kept — you can retry saving."
                )
            else:
                vm["error"] = ""
                vm["saved"] = stored["id"]
                st.rerun()

        if vm.get("show_reference"):
            st.subheader("Reference answer")
            st.write(question["reference_answer"])
            st.write(
                "The reference was revealed, so further practice on this "
                "question is **assisted** for the rest of this session "
                "(pressing Try again does not reset that). Cross-session "
                "assistance cannot be established — a fresh session always "
                "starts unassisted."
            )
            st.write(f"Follow-up to try next: {question['follow_up']}")
        elif st.button("Reveal reference answer", key="reveal_btn"):
            flow.reveal_reference(vm)
            st.rerun()
        else:
            st.caption(
                "Reading the reference makes further practice assisted. "
                "Reveal it explicitly — opening nothing by accident."
            )

        if vm["error"]:
            st.warning(vm["error"])
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
