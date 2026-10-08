"""Tests for the transcription adapter (US-04).

All offline and model-download-free: a clearly labeled FakeTranscriber test
double stands in for the faster-whisper backend. Real-model verification is
a documented manual step, never faked here.
"""

import math
import struct
import sys
import wave

import pytest

from app import transcribe
from app.transcribe import (
    AudioTooLargeError,
    AudioTooLongError,
    DecodingError,
    EmptySpeechError,
    FasterWhisperBackend,
    TranscriberUnavailableError,
    TranscriptionError,
    UnsupportedFormatError,
    speech_stack_available,
    transcribe_audio,
)


class FakeTranscriber:
    """TEST DOUBLE ONLY — canned transcript plus a call log.

    This is not a production fallback and is never used outside tests.
    """

    name = "fake-test-double"

    def __init__(self, text="copies on multiple nodes help availability",
                 language="en", error=None):
        self.text = text
        self.language = language
        self.error = error
        self.calls = []

    def transcribe(self, path):
        self.calls.append(path)
        if self.error is not None:
            raise self.error
        return self.text, self.language


def _make_wav_bytes(path, seconds=2.0, rate=8000):
    frames = b"".join(
        struct.pack("<h", int(10000 * math.sin(2 * math.pi * 440 * t / rate)))
        for t in range(int(seconds * rate))
    )
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(frames)
    return path.read_bytes()


def _tmp_files(tmp_path):
    return [p for p in tmp_path.iterdir()]


# --- Successful path -----------------------------------------------------------------


def test_fake_transcription_returns_transcript_and_metadata(tmp_path):
    data = _make_wav_bytes(tmp_path / "answer.wav", seconds=2.0)
    fake = FakeTranscriber()
    result = transcribe_audio(data, "answer.wav", transcriber=fake, tmpdir=tmp_path)
    assert result["transcript"] == "copies on multiple nodes help availability"
    assert result["language"] == "en"
    assert result["duration_s"] == pytest.approx(2.0, abs=0.1)
    assert result["backend"] == "fake-test-double"
    assert result["model"] == transcribe.DEFAULT_MODEL
    assert "confidence" not in result
    assert len(fake.calls) == 1
    assert _tmp_files(tmp_path) == [tmp_path / "answer.wav"]  # input untouched


def test_duration_is_measured_not_invented(tmp_path):
    data = _make_wav_bytes(tmp_path / "answer.wav", seconds=3.0)
    result = transcribe_audio(
        data, "answer.wav", transcriber=FakeTranscriber(), tmpdir=tmp_path
    )
    assert result["duration_s"] == pytest.approx(3.0, abs=0.1)


# --- Missing dependencies ---


def test_backend_construction_loads_no_model_and_no_imports():
    backend = FasterWhisperBackend()
    assert backend._model is None  # nothing downloaded or loaded on init


def test_missing_speech_libraries_raise_actionable_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "faster_whisper", None)
    with pytest.raises(TranscriberUnavailableError, match="requirements-audio"):
        FasterWhisperBackend().transcribe("whatever.wav")


def test_missing_decoder_library_raise_actionable_error(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "av", None)
    data = _make_wav_bytes(tmp_path / "answer.wav", seconds=1.0)
    with pytest.raises(TranscriberUnavailableError, match="requirements-audio"):
        transcribe_audio(data, "answer.wav", transcriber=FakeTranscriber())


# --- Validation before inference ---


def test_oversized_audio_rejected_before_decoding(tmp_path):
    data = b"\x00" * (transcribe.MAX_AUDIO_BYTES + 1)
    with pytest.raises(AudioTooLargeError, match="20 MB"):
        transcribe_audio(data, "answer.wav", transcriber=FakeTranscriber())
    assert _tmp_files(tmp_path) == []


def test_overlong_audio_rejected_before_inference(tmp_path):
    data = _make_wav_bytes(tmp_path / "long.wav", seconds=200.0)
    fake = FakeTranscriber()
    with pytest.raises(AudioTooLongError, match="180"):
        transcribe_audio(data, "long.wav", transcriber=fake, tmpdir=tmp_path)
    assert fake.calls == []  # inference never ran
    assert _tmp_files(tmp_path) == [tmp_path / "long.wav"]


def test_unsupported_suffix_rejected(tmp_path):
    with pytest.raises(UnsupportedFormatError, match="supported"):
        transcribe_audio(b"data", "answer.exe", transcriber=FakeTranscriber())
    assert _tmp_files(tmp_path) == []


def test_corrupt_audio_raises_decoding_error(tmp_path):
    fake = FakeTranscriber()
    with pytest.raises(DecodingError):
        transcribe_audio(
            b"this is not audio at all" * 100, "answer.wav",
            transcriber=fake, tmpdir=tmp_path,
        )
    assert fake.calls == []
    assert _tmp_files(tmp_path) == []


def test_empty_transcript_raises_empty_speech(tmp_path):
    data = _make_wav_bytes(tmp_path / "answer.wav", seconds=1.0)
    with pytest.raises(EmptySpeechError, match="no speech detected"):
        transcribe_audio(
            data, "answer.wav",
            transcriber=FakeTranscriber(text="   "), tmpdir=tmp_path,
        )
    assert _tmp_files(tmp_path) == [tmp_path / "answer.wav"]


def test_backend_errors_wrapped_but_transcription_errors_pass_through(tmp_path):
    data = _make_wav_bytes(tmp_path / "answer.wav", seconds=1.0)
    with pytest.raises(DecodingError, match="backend failed"):
        transcribe_audio(
            data, "answer.wav",
            transcriber=FakeTranscriber(error=RuntimeError("boom")),
            tmpdir=tmp_path,
        )
    sentinel = EmptySpeechError("from backend")
    with pytest.raises(EmptySpeechError, match="from backend"):
        transcribe_audio(
            data, "answer.wav",
            transcriber=FakeTranscriber(error=sentinel), tmpdir=tmp_path,
        )


def test_invalid_input_types_rejected():
    with pytest.raises(TypeError, match="must be bytes"):
        transcribe_audio("not-bytes", "answer.wav", transcriber=FakeTranscriber())
    with pytest.raises(TranscriptionError, match="no audio data"):
        transcribe_audio(b"", "answer.wav", transcriber=FakeTranscriber())


# --- Temp-file hygiene ---


def test_temp_file_uses_generated_name_not_upload_name(tmp_path, monkeypatch):
    seen = []
    real_write = transcribe._write_temp_file

    def spy(data, suffix, tmpdir=None):
        path = real_write(data, suffix, tmpdir)
        seen.append(path)
        return path

    monkeypatch.setattr(transcribe, "_write_temp_file", spy)
    data = _make_wav_bytes(tmp_path / "in.wav", seconds=1.0)
    transcribe_audio(
        data, "../../evil.wav", transcriber=FakeTranscriber(), tmpdir=tmp_path
    )
    assert len(seen) == 1
    assert seen[0].endswith(".wav")
    assert "evil" not in seen[0]
    assert _tmp_files(tmp_path) == [tmp_path / "in.wav"]  # temp file deleted


def test_speech_stack_check_reflects_reality(monkeypatch):
    assert speech_stack_available() in (True, False)
    monkeypatch.setitem(sys.modules, "faster_whisper", None)
    assert speech_stack_available() is False
