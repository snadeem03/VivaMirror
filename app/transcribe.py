"""Local transcription adapter (US-04).

Single interface with a free, local default backend (faster-whisper on CPU,
int8, small English model). No paid services, no API credentials.

Speech libraries are imported lazily inside functions, so typed practice
starts without them: ``import app.transcribe`` never imports faster-whisper
or av. Call :func:`speech_stack_available` to check before use.

Returns transcript, language (where the backend reports one), audio duration
(where measurable), and backend/model metadata. No confidence values and no
speaking scores are produced — this adapter only turns speech into text.

First run downloads the model (~150 MB, internet + disk + time required);
after that the local model cache makes transcription work offline. A failed
download is reported as :class:`ModelDownloadError`, never hidden.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

BACKEND_NAME = "faster-whisper"
DEFAULT_MODEL = "base.en"
DEFAULT_DEVICE = "cpu"
DEFAULT_COMPUTE_TYPE = "int8"

MAX_AUDIO_BYTES = 20 * 1024 * 1024  # 20 MB, checked before any decoding
MAX_DURATION_S = 180.0  # 3 minutes, checked before expensive inference

# Formats the backend (via PyAV decoding) actually accepts. Anything else is
# rejected before decoding, based on the filename suffix only.
SUPPORTED_SUFFIXES = (".wav", ".mp3", ".m4a", ".ogg", ".oga", ".flac", ".webm")


class TranscriptionError(ValueError):
    """Base class for all transcription failures."""


class TranscriberUnavailableError(TranscriptionError):
    """Speech libraries are not installed."""


class UnsupportedFormatError(TranscriptionError):
    """Filename suffix is outside SUPPORTED_SUFFIXES."""


class AudioTooLargeError(TranscriptionError):
    """Audio exceeds MAX_AUDIO_BYTES."""


class AudioTooLongError(TranscriptionError):
    """Audio exceeds MAX_DURATION_S."""


class DecodingError(TranscriptionError):
    """Audio bytes could not be decoded (corrupt or unsupported content)."""


class ModelDownloadError(TranscriptionError):
    """The transcription model could not be loaded or downloaded."""


class EmptySpeechError(TranscriptionError):
    """Transcription produced no usable text (e.g. silence)."""


def speech_stack_available() -> bool:
    """True when faster-whisper and av import cleanly (no model loaded)."""
    try:
        __import__("faster_whisper")
        __import__("av")
    except ImportError:
        return False
    return True


def _suffix_for(filename_hint: str) -> str:
    suffix = Path(filename_hint or "").suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise UnsupportedFormatError(
            f"unsupported audio format {suffix or '(none)'} for "
            f"'{filename_hint}'; supported: {', '.join(SUPPORTED_SUFFIXES)}"
        )
    return suffix


def _write_temp_file(
    data: bytes, suffix: str, tmpdir: str | Path | None = None
) -> str:
    """Write audio bytes to a safe temp file (generated name, chosen suffix).

    The uploaded filename is never used as a filesystem path. Callers must
    delete the file in a ``finally`` block (see :func:`transcribe_audio`).
    """
    with tempfile.NamedTemporaryFile(
        prefix="vivamirror-audio-",
        suffix=suffix,
        dir=tmpdir,
        delete=False,
    ) as handle:
        handle.write(data)
        return handle.name


def _probe_duration_s(path: str) -> float:
    """Audio duration in seconds without running speech inference.

    WAV (what the microphone widget records) is measured with the standard
    library, so the common path needs no speech stack at all. Other formats
    fall back to PyAV decoding, which reports a clear install hint when the
    optional audio stack is absent.
    """
    if Path(path).suffix.lower() == ".wav":
        try:
            import wave

            with wave.open(path, "rb") as handle:
                frames = handle.getnframes()
                rate = handle.getframerate()
                if rate > 0:
                    return frames / rate
        except Exception as exc:
            raise DecodingError(
                f"could not decode WAV audio ({type(exc).__name__}); the "
                f"file may be corrupt or not real audio"
            ) from exc
        raise DecodingError("could not determine WAV duration from the file")
    try:
        import av
    except ImportError as exc:
        raise TranscriberUnavailableError(
            "audio support is not installed; run "
            "`pip install -r requirements-audio.txt` in the Python 3.11 "
            "environment (typed practice keeps working without it)"
        ) from exc
    try:
        with av.open(path) as container:
            if container.duration is not None:
                return container.duration / 1_000_000
            for stream in container.streams.audio:
                if stream.duration is not None and stream.time_base:
                    return float(stream.duration * stream.time_base)
    except Exception as exc:
        raise DecodingError(
            f"could not decode audio file ({type(exc).__name__}); the file "
            f"may be corrupt or not real audio"
        ) from exc
    raise DecodingError("could not determine audio duration from the file")


class FasterWhisperBackend:
    """Default local backend: faster-whisper on CPU.

    The model object is created on first :meth:`transcribe`, so merely
    constructing this backend never downloads anything.
    """

    name = BACKEND_NAME

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str = DEFAULT_DEVICE,
        compute_type: str = DEFAULT_COMPUTE_TYPE,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise TranscriberUnavailableError(
                "audio support is not installed; run "
                "`pip install -r requirements-audio.txt` in the Python 3.11 "
                "environment (typed practice keeps working without it)"
            ) from exc
        try:
            self._model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
            )
        except Exception as exc:
            raise ModelDownloadError(
                f"could not load transcription model '{self.model_name}' "
                f"({type(exc).__name__}: {exc}); first run downloads ~150 MB "
                f"and needs internet, disk space, and time — with a cached "
                f"model it works offline"
            ) from exc
        return self._model

    def transcribe(self, path: str) -> tuple[str, str | None]:
        """Transcribe an audio file; returns (transcript, language|None)."""
        model = self._load_model()
        try:
            segments, info = model.transcribe(path)
            text = "".join(segment.text for segment in segments).strip()
        except TranscriptionError:
            raise
        except Exception as exc:
            raise DecodingError(
                f"speech inference failed ({type(exc).__name__}: {exc})"
            ) from exc
        language = getattr(info, "language", None)
        return text, language


def transcribe_audio(
    audio_bytes: bytes,
    filename_hint: str = "answer.wav",
    transcriber=None,
    tmpdir: str | Path | None = None,
    model: str = DEFAULT_MODEL,
) -> dict:
    """Transcribe audio bytes; returns transcript plus metadata.

    Validates size, then format, then duration — before expensive inference.
    The audio is staged through a safe temp file that is always deleted
    (success and error paths). ``transcriber`` accepts any object with
    ``transcribe(path) -> (text, language)``; the default is the local
    faster-whisper backend. Never invents confidence or speaking scores.
    """
    if not isinstance(audio_bytes, (bytes, bytearray)):
        raise TypeError(
            f"audio_bytes must be bytes, got {type(audio_bytes).__name__}"
        )
    if not audio_bytes:
        raise TranscriptionError("no audio data was provided")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise AudioTooLargeError(
            f"audio is {len(audio_bytes) / 1_048_576:.1f} MB, above the "
            f"{MAX_AUDIO_BYTES // 1_048_576} MB limit; record a shorter "
            f"answer or type it instead"
        )
    suffix = _suffix_for(filename_hint)
    path = _write_temp_file(bytes(audio_bytes), suffix, tmpdir)
    try:
        duration_s = _probe_duration_s(path)
        if duration_s > MAX_DURATION_S:
            raise AudioTooLongError(
                f"audio is {duration_s:.0f}s, above the "
                f"{MAX_DURATION_S:.0f}s limit; record a shorter answer or "
                f"type it instead"
            )
        if transcriber is None:
            backend = FasterWhisperBackend(model)
        else:
            backend = transcriber
        backend_name = getattr(backend, "name", type(backend).__name__)
        model_name = getattr(backend, "model_name", model)
        try:
            transcript, language = backend.transcribe(path)
        except TranscriptionError:
            raise
        except Exception as exc:
            raise DecodingError(
                f"transcription backend failed "
                f"({type(exc).__name__}: {exc})"
            ) from exc
        if not transcript or not transcript.strip():
            raise EmptySpeechError(
                "no speech detected in the audio (silence or unintelligible "
                "recording); try re-recording closer to the microphone, or "
                "type the answer instead"
            )
        return {
            "transcript": transcript.strip(),
            "language": language,
            "duration_s": duration_s,
            "backend": backend_name,
            "model": model_name,
        }
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
