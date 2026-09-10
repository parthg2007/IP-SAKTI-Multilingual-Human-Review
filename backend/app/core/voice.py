"""Voice transcription service supporting Groq Whisper and Deepgram."""
import os
import logging
from typing import Optional, Dict, Any, Tuple
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class VoiceTranscriptionService:
    """
    Transcribes spoken audio into text using Groq Whisper API (free, high-throughput)
    or optional Deepgram API fallback.
    """

    GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

    def __init__(self):
        self.groq_key: Optional[str] = os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY
        self.groq_whisper_model: str = os.getenv("GROQ_WHISPER_MODEL") or settings.GROQ_WHISPER_MODEL
        self.deepgram_key: Optional[str] = os.getenv("DEEPGRAM_API_KEY") or settings.DEEPGRAM_API_KEY

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        content_type: str = "audio/wav",
        language: Optional[str] = None
    ) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """
        Transcribes audio bytes to text.
        Returns: (transcribed_text, detected_language, metadata)
        """
        groq_key = os.getenv("GROQ_API_KEY") or self.groq_key
        deepgram_key = os.getenv("DEEPGRAM_API_KEY") or self.deepgram_key

        # 1. Try Groq Whisper (Preferred: generous free tier, ultra-fast transcription)
        if groq_key:
            try:
                model_name = os.getenv("GROQ_WHISPER_MODEL") or self.groq_whisper_model
                headers = {"Authorization": f"Bearer {groq_key}"}
                files = {"file": (filename, audio_bytes, content_type)}
                data = {
                    "model": model_name,
                    "response_format": "verbose_json"
                }
                if language and language not in ("auto", ""):
                    data["language"] = language

                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        self.GROQ_AUDIO_URL,
                        headers=headers,
                        files=files,
                        data=data
                    )
                    resp.raise_for_status()
                    result = resp.json()
                    text = result.get("text", "").strip()
                    detected_lang = result.get("language")
                    logger.info(f"Groq Whisper transcribed audio ({len(audio_bytes)} bytes): '{text[:60]}...'")
                    return text, detected_lang, {"provider": "groq_whisper", "model": model_name, "raw": result}
            except Exception as exc:
                logger.error(f"Groq Whisper transcription failed: {exc}")

        # 2. Try Deepgram fallback if configured
        if deepgram_key:
            try:
                dg_url = "https://api.deepgram.com/v1/listen?smart_format=true&model=nova-2"
                if language and language not in ("auto", ""):
                    dg_url += f"&language={language}"
                headers = {
                    "Authorization": f"Token {deepgram_key}",
                    "Content-Type": content_type
                }
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(dg_url, headers=headers, content=audio_bytes)
                    resp.raise_for_status()
                    result = resp.json()
                    transcript = (
                        result.get("results", {})
                        .get("channels", [{}])[0]
                        .get("alternatives", [{}])[0]
                        .get("transcript", "")
                    ).strip()
                    return transcript, language, {"provider": "deepgram", "raw": result}
            except Exception as exc:
                logger.error(f"Deepgram transcription failed: {exc}")

        raise RuntimeError(
            "Voice transcription is not available: GROQ_API_KEY is not set in .env. "
            "Add your free Groq API key to enable Whisper transcription, or use browser Web Speech."
        )


voice_service = VoiceTranscriptionService()

