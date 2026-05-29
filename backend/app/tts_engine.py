"""ReelIQ Backend — multi-tier local TTS engine."""
import math
import struct
import tempfile
import wave
from io import BytesIO
from pathlib import Path
from typing import Dict

from app.config import get_settings

settings = get_settings()

VOICE_PROFILES: Dict[str, Dict[str, object]] = {
    "coqui-professional": {"speaker": None, "speed": 1.0, "frequency": 180},
    "coqui-creator": {"speaker": None, "speed": 1.08, "frequency": 220},
    "coqui-explainer": {"speaker": None, "speed": 0.94, "frequency": 160},
    "coqui-warm": {"speaker": None, "speed": 1.0, "frequency": 205},
}


def synthesize_tts(text: str, voice_id: str = "coqui-professional") -> tuple[bytes, str]:
    """Generate speech bytes using Coqui, then gTTS, then pyttsx3, then WAV tones."""
    clean_text = " ".join(text.split())
    if not clean_text:
        raise ValueError("Text is required")

    profile = VOICE_PROFILES.get(voice_id, VOICE_PROFILES["coqui-professional"])

    for synthesizer in (_try_coqui, _try_gtts, _try_pyttsx3):
        audio = synthesizer(clean_text, profile)
        if audio:
            return audio

    return _procedural_wave(clean_text, int(profile["frequency"])), "wav"


def _try_coqui(text: str, profile: Dict[str, object]) -> tuple[bytes, str] | None:
    try:
        from TTS.api import TTS

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as output:
            output_path = Path(output.name)

        try:
            tts = TTS(settings.COQUI_TTS_MODEL)
            tts.tts_to_file(text=text, file_path=str(output_path), speaker=profile.get("speaker"))
            return output_path.read_bytes(), "wav"
        finally:
            output_path.unlink(missing_ok=True)
    except Exception:
        return None


def _try_gtts(text: str, profile: Dict[str, object]) -> tuple[bytes, str] | None:
    try:
        from gtts import gTTS

        buffer = BytesIO()
        gTTS(text=text, lang="en", slow=float(profile["speed"]) < 1.0).write_to_fp(buffer)
        return buffer.getvalue(), "mp3"
    except Exception:
        return None


def _try_pyttsx3(text: str, profile: Dict[str, object]) -> tuple[bytes, str] | None:
    try:
        import pyttsx3

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as output:
            output_path = Path(output.name)

        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", int(175 * float(profile["speed"])))
            engine.save_to_file(text, str(output_path))
            engine.runAndWait()
            return output_path.read_bytes(), "wav"
        finally:
            output_path.unlink(missing_ok=True)
    except Exception:
        return None


def _procedural_wave(text: str, base_frequency: int) -> bytes:
    sample_rate = 22050
    seconds = min(max(len(text.split()) / 2.6, 1.2), 20.0)
    total_samples = int(sample_rate * seconds)
    buffer = BytesIO()

    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        for index in range(total_samples):
            progress = index / sample_rate
            syllable = int(progress * 6) % 5
            frequency = base_frequency + syllable * 28
            envelope = min(1.0, index / (sample_rate * 0.05), (total_samples - index) / (sample_rate * 0.08))
            sample = int(9000 * envelope * math.sin(2 * math.pi * frequency * progress))
            wav.writeframes(struct.pack("<h", sample))

    return buffer.getvalue()
