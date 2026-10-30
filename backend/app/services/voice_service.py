"""ElevenLabs Speech-to-Text (`scribe_v1`) and Text-to-Speech (`eleven_flash_v2_5`) Service."""
import base64
from typing import Optional
import httpx
from fastapi import HTTPException

from app.config import settings
from app.models.schemas import SynthesizeResponse, TranscribeResponse

MOCK_SILENT_MP3_BASE64 = (
    "//uQxAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAACAAABIADAwMDAwMDAwMDA"
    "wMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA"
)


async def transcribe_audio_bytes(
    audio_bytes: bytes,
    filename: str = "recording.webm",
    content_type: str = "audio/webm",
    language_code: Optional[str] = None,
) -> TranscribeResponse:
    """Transcribe user speech using ElevenLabs Scribe (`POST /v1/speech-to-text`)."""
    if not settings.ELEVENLABS_API_KEY:
        raise HTTPException(status_code=503, detail="Voice input is unavailable. Please type your message.")

    url = "https://api.elevenlabs.io/v1/speech-to-text"
    headers = {"xi-api-key": settings.ELEVENLABS_API_KEY}
    data: dict[str, str] = {"model_id": settings.ELEVENLABS_STT_MODEL}
    if language_code:
        data["language_code"] = language_code

    files = {"file": (filename, audio_bytes, content_type)}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, headers=headers, data=data, files=files)
            resp.raise_for_status()
            payload = resp.json()
            text = payload.get("text", "").strip()
            if not text:
                raise HTTPException(status_code=422, detail="No speech was detected. Please try again or type your message.")
            return TranscribeResponse(
                text=text,
                language_code=payload.get("language_code") or language_code or "en",
                provider=settings.ELEVENLABS_STT_MODEL,
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="Voice transcription failed. Please try again or type your message.") from None



async def synthesize_keeper_speech(
    text: str,
    voice_id: Optional[str] = None,
) -> SynthesizeResponse:
    """Generate spoken audio from text using ElevenLabs (`POST /v1/text-to-speech/{voice_id}`)."""
    target_voice = voice_id or settings.ELEVENLABS_VOICE_ID

    if not settings.ELEVENLABS_API_KEY:
        return SynthesizeResponse(
            audio_base64=MOCK_SILENT_MP3_BASE64,
            mime_type="audio/mpeg",
            provider="mock_elevenlabs_flash_v2_5",
        )

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{target_voice}"
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": settings.ELEVENLABS_TTS_MODEL,
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.80,
            "style": 0.35,
            "use_speaker_boost": True,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            b64_audio = base64.b64encode(resp.content).decode("utf-8")
            return SynthesizeResponse(
                audio_base64=b64_audio,
                mime_type="audio/mpeg",
                provider=settings.ELEVENLABS_TTS_MODEL,
            )
    except Exception:
        return SynthesizeResponse(
            audio_base64=MOCK_SILENT_MP3_BASE64,
            mime_type="audio/mpeg",
            provider="mock_elevenlabs_flash_v2_5_fallback",
        )
