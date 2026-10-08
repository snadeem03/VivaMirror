"""Spoken-answer UI tests (US-03/US-04 slice) via AppTest.

The real upload widget is driven with real audio bytes through the real
``transcribe_audio`` path; only the speech backend is a clearly labeled
FakeTranscriber test double (never a production fallback). The microphone
widget renders for real browsers but has no AppTest accessor, so mic
recording itself is a documented manual check.
"""

import io
import math
import struct
import sys
import wave
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app import transcribe as transcribe_module

MAIN = str(Path(__file__).resolve().parent.parent / "app" / "main.py")

PARTIAL_DS15 = (
    "Since network splits will eventually happen, I must choose between "
    "consistency and availability."
)


class FakeTranscriber:
    """TEST DOUBLE ONLY — canned transcript plus a call log."""

    name = "fake-test-double"

    def __init__(self, text="copies on multiple nodes help availability",
                 error=None):
        self.text = text
        self.error = error
        self.calls = []

    def transcribe(self, path):
        self.calls.append(path)
        if self.error is not None:
            raise self.error
        return self.text, "en"


def _wav_bytes(seconds=1.0, rate=8000):
    frames = b"".join(
        struct.pack("<h", int(8000 * math.sin(2 * math.pi * 440 * t / rate)))
        for t in range(int(seconds * rate))
    )
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(frames)
    return buffer.getvalue()


def _run(transcriber=None):
    at = AppTest.from_file(MAIN)
    if transcriber is not None:
        at.session_state["vm_transcriber"] = transcriber
    at.run()
    assert not at.exception, f"script raised: {at.exception}"
    return at


def _labels(at):
    return [option for option in at.selectbox(key="question_select").options]


def _select(at, idx):
    at.selectbox(key="question_select").set_value(_labels(at)[idx]).run()
    assert not at.exception
    return at


def _headers(at):
    return [h.value for h in at.header]


def _speak(at, wav_bytes=None, name="answer.wav"):
    """Switch to spoken mode and provide audio through the real uploader."""
    at.radio(key="mode_radio").set_value("Spoken answer").run()
    at.file_uploader(key="upload_input").set_value(
        (name, wav_bytes if wav_bytes is not None else _wav_bytes(), "audio/wav")
    ).run()
    return at


def _transcribe(at):
    at.button(key="transcribe_btn").click().run()
    assert not at.exception
    return at


# --- Typed independence ----------------------------------------------------------------------


def test_typed_flow_works_when_speech_stack_is_absent(monkeypatch):
    monkeypatch.setitem(sys.modules, "faster_whisper", None)
    monkeypatch.setitem(sys.modules, "av", None)
    assert transcribe_module.speech_stack_available() is False

    at = _run()
    _select(at, 14)
    at.text_area(key="draft_input").set_value(PARTIAL_DS15).run()
    at.button(key="review_btn").click().run()
    at.button(key="evaluate_btn").click().run()
    assert "Concept coverage: 65.0%" in _headers(at)


def test_read_upload_normalizes_mic_and_upload_shapes():
    from app.main import _read_upload

    class StubUpload:
        type = "audio/wav"
        name = "mic-recording.wav"

        def getvalue(self):
            return b"\x01\x02"

    assert _read_upload(StubUpload()) == {
        "data": b"\x01\x02",
        "mime": "audio/wav",
        "name": "mic-recording.wav",
    }


# --- Spoken flow ---------------------------------------------------------------------------------


def test_successful_transcription_enters_review_not_evaluation():
    fake = FakeTranscriber()
    at = _run(fake)
    _select(at, 9)  # ds-10 matches the canned transcript
    _speak(at)
    _transcribe(at)
    assert len(fake.calls) == 1
    assert not any("Concept coverage" in h for h in _headers(at))
    assert "copies on multiple nodes help availability" in [
        t.value for t in at.text
    ]


def test_transcript_edit_feeds_the_evaluator():
    fake = FakeTranscriber()
    at = _run(fake)
    _select(at, 14)
    _speak(at)
    _transcribe(at)
    at.text_area(key="review_input").set_value(PARTIAL_DS15).run()
    at.button(key="evaluate_btn").click().run()
    assert "Concept coverage: 65.0%" in _headers(at)


def test_reruns_do_not_retranscribe():
    fake = FakeTranscriber()
    at = _run(fake)
    _select(at, 9)
    _speak(at)
    _transcribe(at)
    at.run()
    at.run()
    assert len(fake.calls) == 1


def test_question_change_invalidates_audio_and_transcript():
    fake = FakeTranscriber()
    at = _run(fake)
    _select(at, 9)
    _speak(at)
    _transcribe(at)
    assert len(fake.calls) == 1
    _select(at, 7)
    assert not any("Concept coverage" in h for h in _headers(at))
    assert at.file_uploader(key="upload_input").value is None
    assert at.expander == []
    assert len(fake.calls) == 1


def test_mode_switch_preserves_inputs_but_clears_result():
    fake = FakeTranscriber()
    at = _run(fake)
    _select(at, 9)
    at.radio(key="mode_radio").set_value("Typed answer").run()
    at.text_area(key="draft_input").set_value("my typed words").run()
    at.radio(key="mode_radio").set_value("Spoken answer").run()
    _speak(at, _wav_bytes())
    _transcribe(at)
    at.text_area(key="review_input").set_value(
        "copies on multiple nodes help availability"
    ).run()
    at.button(key="evaluate_btn").click().run()
    assert "Concept coverage: 30.0%" in _headers(at)

    at.radio(key="mode_radio").set_value("Typed answer").run()
    assert not any("Concept coverage" in h for h in _headers(at))
    assert at.text_area(key="draft_input").value == "my typed words"


def test_oversized_audio_rejected_before_transcription():
    fake = FakeTranscriber()
    at = _run(fake)
    _select(at, 9)
    at.radio(key="mode_radio").set_value("Spoken answer").run()
    big = b"\x00" * (transcribe_module.MAX_AUDIO_BYTES + 1)
    at.file_uploader(key="upload_input").set_value(
        ("big.wav", big, "audio/wav")
    ).run()
    at.button(key="transcribe_btn").click().run()
    assert not any("Concept coverage" in h for h in _headers(at))
    assert at.warning, "expected a size-limit message"
    assert "20 MB" in at.warning[0].value
    assert len(fake.calls) == 0


def test_corrupt_audio_shows_helpful_error_and_keeps_typed_fallback():
    fake = FakeTranscriber()
    at = _run(fake)
    _select(at, 9)
    at.radio(key="mode_radio").set_value("Spoken answer").run()
    at.file_uploader(key="upload_input").set_value(
        ("answer.wav", b"garbage-bytes" * 100, "audio/wav")
    ).run()
    at.button(key="transcribe_btn").click().run()
    assert not any("Concept coverage" in h for h in _headers(at))
    assert at.warning, "expected a decoding-failure message"
    assert "type the answer" in at.warning[0].value.lower()

    at.radio(key="mode_radio").set_value("Typed answer").run()
    at.text_area(key="draft_input").set_value(
        "copies on multiple nodes help availability"
    ).run()
    at.button(key="review_btn").click().run()
    at.button(key="evaluate_btn").click().run()
    assert "Concept coverage: 30.0%" in _headers(at)


def test_backend_failure_reports_and_offers_typed_mode():
    fake = FakeTranscriber(error=RuntimeError("engine exploded"))
    at = _run(fake)
    _select(at, 9)
    _speak(at)
    _transcribe(at)
    assert not any("Concept coverage" in h for h in _headers(at))
    assert at.warning
    assert "type the answer" in at.warning[0].value.lower()


def test_no_audio_files_written_to_the_repo():
    root = Path(__file__).resolve().parent.parent
    watched = ["app", "data", "docs", "tests"]

    def snapshot():
        files = set()
        for part in watched:
            files |= {str(p) for p in (root / part).rglob("*") if p.is_file()}
        files |= {str(p) for p in root.glob("*") if p.is_file()}
        return files

    before = snapshot()
    fake = FakeTranscriber()
    at = _run(fake)
    _select(at, 9)
    _speak(at)
    _transcribe(at)
    at.button(key="evaluate_btn").click().run()
    assert "Concept coverage: 30.0%" in _headers(at)
    assert snapshot() == before


@pytest.mark.parametrize("idx", [9, 14])
def test_spoken_answer_caption_names_transcribed_mode(idx):
    fake = FakeTranscriber()
    at = _run(fake)
    _select(at, idx)
    _speak(at)
    _transcribe(at)
    at.button(key="evaluate_btn").click().run()
    captions = [c.value for c in at.caption]
    assert any("spoken answer (transcribed)" in c for c in captions)
