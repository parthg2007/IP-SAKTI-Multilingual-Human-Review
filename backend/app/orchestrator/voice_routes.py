"""Voice transcription API router for IP-SAKTI."""
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel

from app.core.voice import voice_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/voice", tags=["Voice Support"])


class VoiceTranscriptionResponse(BaseModel):
    text: str
    language: Optional[str] = None
    provider: str
    status: str = "success"


@router.post("/transcribe", response_model=VoiceTranscriptionResponse)
async def transcribe_voice(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None)
):
    """
    Transcribes audio file to text using Groq Whisper (or Deepgram fallback).
    Supports WAV, WebM, MP3, OGG, and M4A audio from browser microphones.
    """
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio file was uploaded."
        )

    try:
        content = await file.read()
        if len(content) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded audio is empty or corrupted."
            )

        filename = file.filename or "recording.webm"
        content_type = file.content_type or "audio/webm"

        text, detected_lang, meta = await voice_service.transcribe_audio(
            audio_bytes=content,
            filename=filename,
            content_type=content_type,
            language=language
        )

        return VoiceTranscriptionResponse(
            text=text,
            language=detected_lang,
            provider=meta.get("provider", "groq_whisper"),
            status="success"
        )
    except HTTPException:
        raise
    except RuntimeError as rerr:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(rerr)
        )
    except Exception as exc:
        logger.error(f"Failed to process voice transcription: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio transcription failed: {str(exc)}"
        )
