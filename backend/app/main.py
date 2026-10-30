"""Candy or Curse? — FastAPI Main Application (Team B)."""
import base64
import re
from typing import Any, Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    CreateSessionRequest,
    IdentificationStatus,
    IngredientSource,
    RecognizedProduct,
    ScanResult,
    SessionResponse,
    SynthesizeRequest,
    SynthesizeResponse,
    TranscribeResponse,
)
from app.services.classifier import PRODUCTS_DB, classify_product_for_session
from app.services.gemma_service import chat_with_candy_keeper, recognize_candy_image
from app.services.session_store import session_store
from app.services.voice_service import synthesize_keeper_speech, transcribe_audio_bytes

app = FastAPI(
    title="Candy or Curse? API",
    description=(
        "AI Food & Halloween Candy Scanner Backend powered by Gemma 4 Vision (Front-of-pack + Ingredient OCR), "
        "ElevenLabs Voice Coaching, Recommended Alternatives, and a Verified Ingredient Classification Engine."
    ),
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["System"])
async def health_check() -> dict[str, Any]:
    """Return service health and configuration readiness."""
    return {
        "status": "ok",
        "service": "candy-or-curse-backend",
        "gemma_model": settings.GEMMA_MODEL,
        "gemma_api_configured": bool(settings.GEMINI_API_KEY),
        "elevenlabs_api_configured": bool(settings.ELEVENLABS_API_KEY),
        "verified_products_count": len(PRODUCTS_DB),
        "features": [
            "front_of_pack_recognition",
            "back_of_pack_ingredient_ocr",
            "manual_ingredient_text_input",
            "recommended_alternatives",
            "live_stream_voice_coaching",
        ],
    }


@app.get("/api/products", tags=["Catalog"])
async def list_verified_products() -> dict[str, Any]:
    """Return the verified candy catalog (15 products) for reference and demo testing."""
    return {
        "count": len(PRODUCTS_DB),
        "products": PRODUCTS_DB,
    }


@app.post(
    "/api/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Sessions"],
)
async def create_session(req: Optional[CreateSessionRequest] = None) -> SessionResponse:
    """Create a new scanning session with dietary preferences/allergies and return QR session metadata."""
    payload = req or CreateSessionRequest()
    return session_store.create_session(payload)


@app.get(
    "/api/sessions/{session_id}",
    response_model=SessionResponse,
    tags=["Sessions"],
)
async def get_session(session_id: str) -> SessionResponse:
    """Retrieve current session state, active dietary profile, and mobile scan history."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return session


@app.post(
    "/api/sessions/{session_id}/chat",
    response_model=ChatResponse,
    tags=["Chat & Gemma 4"],
)
async def chat_with_session(session_id: str, req: ChatRequest) -> ChatResponse:
    """Communicate with The Candy Keeper (Gemma 4) and update session dietary restrictions."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    reply, new_restrictions = await chat_with_candy_keeper(
        user_message=req.message,
        current_profile=session.dietary_profile,
    )
    updated_session = session_store.update_dietary_profile(
        session_id=session_id,
        user_message=req.message,
        assistant_reply=reply,
        new_restrictions=new_restrictions,
    )
    assert updated_session is not None
    return ChatResponse(
        session_id=session_id,
        reply=reply,
        updated_dietary_profile=updated_session.dietary_profile,
        extracted_new_restrictions=new_restrictions,
    )


@app.post(
    "/api/sessions/{session_id}/scan",
    response_model=ScanResult,
    tags=["Scanning & Classification"],
)
async def scan_candy(
    session_id: str,
    request: Request,
    demo_product_hint: Optional[str] = Query(
        default=None,
        description="Optional product slug (e.g. 'haribo-goldbears', 'water-bottle-front', 'capri-sun-multivitamin')",
    ),
) -> ScanResult:
    """Scan a food/candy image (front OR ingredient label) or raw ingredient text and get classification + alternatives."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    content_type = request.headers.get("content-type", "").lower()
    image_bytes = b""
    mime_type = "image/jpeg"
    hint = demo_product_hint
    ingredient_text_override: Optional[str] = None

    if "application/json" in content_type:
        body = await request.json()
        b64_str = body.get("image_base64") or ""
        mime_type = body.get("mime_type") or "image/jpeg"
        hint = hint or body.get("demo_product_hint")
        ingredient_text_override = body.get("ingredient_text_override")
        if b64_str:
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]
            try:
                image_bytes = base64.b64decode(b64_str)
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"Invalid base64 image: {exc}") from exc
    elif "multipart/form-data" in content_type:
        form = await request.form()
        upload = form.get("image")
        form_hint = form.get("demo_product_hint")
        form_ing = form.get("ingredient_text_override")
        if isinstance(form_hint, str) and form_hint.strip():
            hint = hint or form_hint.strip()
        if isinstance(form_ing, str) and form_ing.strip():
            ingredient_text_override = form_ing.strip()
        if upload is not None and hasattr(upload, "read"):
            image_bytes = await upload.read()  # type: ignore[misc]
            mime_type = getattr(upload, "content_type", None) or "image/jpeg"

    if not image_bytes and not hint and not ingredient_text_override:
        raise HTTPException(
            status_code=400,
            detail="Provide an 'image' file, 'image_base64', or 'ingredient_text_override'.",
        )

    # If user typed/pasted an ingredient list directly without an image
    if ingredient_text_override and not image_bytes and not hint:
        typed_list = [
            tok.strip()
            for tok in re.split(r"[,;\n]+", ingredient_text_override)
            if tok.strip()
        ]
        recognized_product = RecognizedProduct(
            product_id=None,
            name="Custom Ingredient Label",
            brand=None,
            category="custom_food",
            confidence=0.98,
            visual_evidence="User provided ingredient list text directly.",
        )
        scan_result = classify_product_for_session(
            session_id=session_id,
            recognized=recognized_product,
            identification_status=IdentificationStatus.IDENTIFIED,
            dietary_profile=session.dietary_profile,
            ocr_or_typed_ingredients=typed_list,
            ingredient_source_override=IngredientSource.USER_TEXT_INPUT,
        )
        session_store.record_scan(session_id, scan_result)
        return scan_result

    (
        recognized_product,
        identification_status,
        uncertainty_reasons,
        ocr_ingredients,
    ) = await recognize_candy_image(
        image_bytes=image_bytes,
        mime_type=mime_type,
        demo_product_hint=hint,
    )

    custom_ingredients = ocr_ingredients
    source_override: Optional[IngredientSource] = (
        IngredientSource.PACKAGE_OCR if ocr_ingredients else None
    )
    if ingredient_text_override:
        custom_ingredients = [
            tok.strip()
            for tok in re.split(r"[,;\n]+", ingredient_text_override)
            if tok.strip()
        ]
        source_override = IngredientSource.USER_TEXT_INPUT

    scan_result = classify_product_for_session(
        session_id=session_id,
        recognized=recognized_product,
        identification_status=identification_status,
        dietary_profile=session.dietary_profile,
        uncertainty_reasons=uncertainty_reasons,
        ocr_or_typed_ingredients=custom_ingredients,
        ingredient_source_override=source_override,
    )
    session_store.record_scan(session_id, scan_result)
    return scan_result


@app.post(
    "/api/voice/transcribe",
    response_model=TranscribeResponse,
    tags=["ElevenLabs Voice"],
)
async def transcribe_voice(
    audio: UploadFile = File(..., description="Recorded audio blob (webm/wav/mp3/mp4)"),
    language_code: Optional[str] = Form(default=None),
) -> TranscribeResponse:
    """Transcribe spoken dietary restrictions using ElevenLabs Speech-to-Text (`scribe_v1`)."""
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty")
    return await transcribe_audio_bytes(
        audio_bytes=audio_bytes,
        filename=audio.filename or "recording.webm",
        content_type=audio.content_type or "audio/webm",
        language_code=language_code,
    )


@app.post(
    "/api/voice/synthesize",
    response_model=SynthesizeResponse,
    tags=["ElevenLabs Voice"],
)
async def synthesize_voice(req: SynthesizeRequest) -> SynthesizeResponse:
    """Synthesize spoken audio for The Candy Keeper using ElevenLabs TTS (`eleven_flash_v2_5`)."""
    return await synthesize_keeper_speech(text=req.text, voice_id=req.voice_id)
