"""Pydantic models for the Candy or Curse API Contract."""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ClassificationStatus(str, Enum):
    GREEN = "GREEN"
    RED = "RED"
    YELLOW = "YELLOW"


class IdentificationStatus(str, Enum):
    IDENTIFIED = "IDENTIFIED"
    NEEDS_INGREDIENT_LABEL = "NEEDS_INGREDIENT_LABEL"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"


class IngredientSource(str, Enum):
    VERIFIED_DATABASE = "VERIFIED_DATABASE"
    PACKAGE_OCR = "PACKAGE_OCR"
    USER_TEXT_INPUT = "USER_TEXT_INPUT"
    UNVERIFIED_FALLBACK = "UNVERIFIED_FALLBACK"
    NONE = "NONE"


class DietaryProfile(BaseModel):
    allergies: list[str] = Field(default_factory=list, description="Explicit allergens such as peanuts, milk, wheat")
    dietary_preferences: list[str] = Field(
        default_factory=list,
        description="Preferences such as halal, vegan, vegetarian, no_gelatin, eat_everything, kosher, gluten_free",
    )
    raw_notes: str = Field(default="", description="User's natural-language restriction notes")
    parsed_restrictions: list[str] = Field(
        default_factory=list,
        description="Normalized canonical restriction tags used by the deterministic classifier",
    )


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str
    timestamp: str


class RecognizedProduct(BaseModel):
    product_id: Optional[str] = Field(default=None, description="Canonical slug from products.json if matched")
    name: str = Field(..., description="Display name of recognized food/candy or 'Unknown Product'")
    brand: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    visual_evidence: str = Field(default="", description="Brief description of visual cues observed by Gemma 4")


class AlternativeProduct(BaseModel):
    product_id: str
    name: str
    brand: str
    category: str
    reason: str = Field(..., description="Why this alternative fits the user's dietary preferences")


class UncertaintyInfo(BaseModel):
    is_uncertain: bool = Field(default=False)
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)


class ScanResult(BaseModel):
    scan_id: str
    session_id: str
    timestamp: str
    recognized_product: RecognizedProduct
    identification_status: IdentificationStatus
    ingredient_source: IngredientSource
    classification: ClassificationStatus
    headline: str
    conflicting_ingredients: list[str] = Field(default_factory=list)
    verified_ingredients: list[str] = Field(default_factory=list)
    allergen_warnings: list[str] = Field(default_factory=list)
    recommended_alternatives: list[AlternativeProduct] = Field(
        default_factory=list,
        description="Compatible alternative products suggested when classification is RED",
    )
    needs_ingredient_photo: bool = Field(
        default=False,
        description="True when the user filmed the front of an unknown product and should turn it around to show the ingredients",
    )
    agent_guidance_prompt: Optional[str] = Field(
        default=None,
        description="Conversational instruction such as 'Okay, turn it around. Let me see the ingredients.'",
    )
    explanation: str
    keeper_spoken_summary: str
    uncertainty: UncertaintyInfo
    safety_disclaimer: str = Field(
        default=(
            "Classification is based on our verified reference database or package OCR. "
            "Formulations vary by region and batch—always read the physical package label before consuming."
        )
    )


class CreateSessionRequest(BaseModel):
    initial_message: Optional[str] = Field(default=None, description="Natural language dietary statement")
    allergies: list[str] = Field(default_factory=list)
    dietary_preferences: list[str] = Field(default_factory=list)


class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    mobile_scan_path: str
    mobile_scan_url: str
    dietary_profile: DietaryProfile
    chat_history: list[ChatMessage] = Field(default_factory=list)
    scan_history: list[ScanResult] = Field(default_factory=list)
    latest_scan: Optional[ScanResult] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User chat message or voice transcript")


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    updated_dietary_profile: DietaryProfile
    extracted_new_restrictions: list[str] = Field(default_factory=list)


class ScanBase64Request(BaseModel):
    image_base64: Optional[str] = Field(default=None, description="Base64-encoded image or data URL")
    mime_type: str = Field(default="image/jpeg")
    ingredient_text_override: Optional[str] = Field(
        default=None,
        description="Optional raw ingredient list text pasted or typed by the user for higher accuracy",
    )
    scan_mode: str = Field(
        default="auto",
        description="'auto', 'front', 'ingredients', or 'live_stream'",
    )
    demo_product_hint: Optional[str] = Field(
        default=None,
        description="Optional product hint (e.g. 'haribo-goldbears', 'water-bottle-front') for deterministic testing",
    )


class TranscribeResponse(BaseModel):
    text: str
    language_code: str = "en"
    provider: str = "elevenlabs_scribe_v1"


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    voice_id: Optional[str] = None


class SynthesizeResponse(BaseModel):
    audio_base64: str
    mime_type: str = "audio/mpeg"
    provider: str = "elevenlabs_flash_v2_5"
