"""
Live subtitle service using OpenAI Whisper.
Receives raw PCM audio bytes over WebSocket, returns transcribed text.
"""
import io
import wave
import logging
import asyncio
import tempfile
import os

from typing import Optional

try:
    import whisper
except ImportError:
    whisper = None

logger = logging.getLogger(__name__)

_whisper_model: Optional[object] = None


def _load_model(size: str = "base"):
    global _whisper_model
    if _whisper_model is None:
        if whisper is None:
            logger.warning("openai-whisper not installed — subtitles disabled.")
            return None
        logger.info(f"Loading Whisper model '{size}'…")
        _whisper_model = whisper.load_model(size)
        logger.info("Whisper model loaded.")
    return _whisper_model


def _pcm_to_wav_bytes(pcm_bytes: bytes, sample_rate: int = 16000, channels: int = 1) -> bytes:
    """Wrap raw PCM in a WAV container so Whisper can read it."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)          # 16-bit PCM
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


async def transcribe_chunk(audio_bytes: bytes, sample_rate: int = 16000) -> str:
    """
    Transcribe a chunk of audio bytes.
    Returns the transcribed text or empty string on error.
    """
    model = _load_model()
    if model is None:
        return ""

    def _run():
        try:
            wav_bytes = _pcm_to_wav_bytes(audio_bytes, sample_rate)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(wav_bytes)
                tmp_path = tmp.name
            try:
                result = model.transcribe(tmp_path, fp16=False, language=None)
                return result.get("text", "").strip()
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except Exception as e:
            logger.error(f"Whisper error: {e}")
            return ""

    return await asyncio.get_event_loop().run_in_executor(None, _run)