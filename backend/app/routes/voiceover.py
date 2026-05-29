"""ReelIQ — Voiceover Generation Routes"""
from fastapi import APIRouter, Depends, HTTPException
from app.models import User
from app.schemas import VoiceoverRequest, VoiceoverResponse
from app.routes.auth import get_optional_user
from app.storage import upload_audio, get_audio_url
from app.tts_engine import synthesize_tts

router = APIRouter(prefix="/voiceover", tags=["Voiceover"])


@router.post("/generate", response_model=VoiceoverResponse)
async def generate_voiceover(
    request: VoiceoverRequest,
    current_user: User | None = Depends(get_optional_user),
):
    try:
        audio_bytes, extension = synthesize_tts(request.text, request.voice_id or "coqui-professional")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    key = upload_audio(audio_bytes, f"voiceover.{extension}")
    return VoiceoverResponse(
        audio_url=get_audio_url(key),
        characters_used=len(request.text),
    )
