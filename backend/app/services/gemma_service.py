"""Gemma 4 Vision and Conversational AI Service (Developer B1).

Uses Google AI Studio / Gemini API (`gemma-4-26b-a4b-it` or `gemma-4-31b-it`) for:
1. Multimodal Candy Wrapper Recognition (`recognize_candy_image`)
2. Conversational "Candy Keeper" Chat & Dietary Extraction (`chat_with_candy_keeper`)

CRITICAL RULE:
Gemma 4 must NEVER invent or guess ingredient lists. It only identifies the product,
reports visual evidence and confidence/uncertainty, and extracts user dietary restrictions.
All ingredient lists come strictly from `backend/app/data/products.json`.
"""
import base64
import json
import re
from typing import Any, Optional
import httpx

from app.config import settings
from app.models.schemas import (
    DietaryProfile,
    IdentificationStatus,
    RecognizedProduct,
)
from app.services.classifier import PRODUCTS_DB, extract_restrictions_from_text

CATALOG_SUMMARY = "\n".join(
    f"- {p['product_id']}: {p['name']} (Brand: {p['brand']}, Visual cues: {p['visual_cues']})"
    for p in PRODUCTS_DB
)

VISION_SYSTEM_PROMPT = f"""You are the visual recognition engine for "Candy or Curse?".
Analyze the user's photo of a packaged candy, snack, or beverage.

Known Verified Catalog:
{CATALOG_SUMMARY}

STRICT RULES:
1. NEVER invent or output ingredient lists. Ingredients are retrieved separately from our verified database.
2. If the image clearly shows one of the known catalog products, set "product_id" to that exact slug and "identification_status" to "IDENTIFIED".
3. If the image shows a recognizable candy NOT in the catalog, set "product_id" to null, "name" to the visible product name, and "identification_status" to "IDENTIFIED".
4. If the image is blurry, dark, occluded, shows multiple conflicting wrappers, or is not a candy/food item, set "identification_status" to "AMBIGUOUS" or "UNKNOWN" and list clear reasons in "uncertainty_reasons".
5. Respond ONLY with valid JSON matching this exact structure:
{{
  "product_id": "haribo-goldbears" | null,
  "name": "Haribo Goldbears (Goldbären)",
  "brand": "Haribo" | null,
  "category": "gummy_candy" | null,
  "confidence": 0.94,
  "identification_status": "IDENTIFIED" | "AMBIGUOUS" | "UNKNOWN",
  "visual_evidence": "Brief description of wrapper colors, logo, and shape visible.",
  "uncertainty_reasons": []
}}
"""

CHAT_SYSTEM_PROMPT = """You are "The Candy Keeper", a theatrical, playful, Halloween-themed AI guardian of the trick-or-treat cauldron.
Your job:
1. Converse in a fun, spooky Halloween persona (2-3 sentences max).
2. Listen carefully for any dietary restrictions, allergies, religious dietary rules (halal, kosher), or ingredient avoidances (vegan, vegetarian, no gelatin, peanuts, tree nuts, milk/dairy/lactose, gluten/wheat, soy, eggs).
3. NEVER claim any candy is "100% allergy-safe" or invent ingredient lists.
4. Respond ONLY with valid JSON matching this exact structure:
{
  "reply": "Spooky in-character response acknowledging their restrictions and inviting them to scan a candy wrapper.",
  "extracted_restrictions": ["peanuts", "vegan", "no_gelatin"]
}
"""


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    """Safely extract a JSON object from model output (stripping markdown fences if present)."""
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end >= start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


async def recognize_candy_image(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    demo_product_hint: Optional[str] = None,
) -> tuple[RecognizedProduct, IdentificationStatus, list[str]]:
    """Identify a packaged candy from image bytes using Gemma 4 Vision.

    Falls back to deterministic hint/mock recognition when GEMINI_API_KEY is not configured
    or if an explicit `demo_product_hint` is passed during testing.
    """
    # 1. Deterministic hint override for automated tests or mock/demo mode
    if demo_product_hint:
        hint = demo_product_hint.strip().lower()
        if hint in {"unknown", "blurry", "ambiguous"}:
            return (
                RecognizedProduct(
                    product_id=None,
                    name="Unknown Wrapper",
                    brand=None,
                    category=None,
                    confidence=0.32,
                    visual_evidence="Wrapper text is obscured or unrecognized.",
                ),
                IdentificationStatus.UNKNOWN,
                ["Image is unclear or product is not recognizable."],
            )
        for p in PRODUCTS_DB:
            if p["product_id"] == hint or hint in [a.lower() for a in p.get("aliases", [])]:
                return (
                    RecognizedProduct(
                        product_id=p["product_id"],
                        name=p["name"],
                        brand=p["brand"],
                        category=p["category"],
                        confidence=0.95,
                        visual_evidence=p["visual_cues"],
                    ),
                    IdentificationStatus.IDENTIFIED,
                    [],
                )
        # Hint is a named product not in our verified DB -> triggers YELLOW
        return (
            RecognizedProduct(
                product_id=None,
                name=demo_product_hint,
                brand="Unverified Brand",
                category="candy",
                confidence=0.82,
                visual_evidence=f"Wrapper resembles {demo_product_hint}.",
            ),
            IdentificationStatus.IDENTIFIED,
            [f"'{demo_product_hint}' is not in the verified 15-product database."],
        )

    # 2. If GEMINI_API_KEY is not set, return a realistic fallback so dev never blocks
    if not settings.GEMINI_API_KEY:
        default_prod = PRODUCTS_DB[0]  # Haribo Goldbears
        return (
            RecognizedProduct(
                product_id=default_prod["product_id"],
                name=default_prod["name"],
                brand=default_prod["brand"],
                category=default_prod["category"],
                confidence=0.91,
                visual_evidence=(
                    "[Mock Vision Mode - Set GEMINI_API_KEY for live Gemma 4 Vision] "
                    + default_prod["visual_cues"]
                ),
            ),
            IdentificationStatus.IDENTIFIED,
            [],
        )

    # 3. Call Google AI Studio Gemini API with Gemma 4 (`gemma-4-26b-a4b-it` or `gemma-4-31b-it`)
    b64_data = base64.b64encode(image_bytes).decode("utf-8")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.GEMMA_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    )
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": VISION_SYSTEM_PROMPT},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_data,
                        }
                    },
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 512,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            text_out = (
                data["candidates"][0]["content"]["parts"][0]["text"]
            )
            parsed = _extract_json_object(text_out)

            status_str = str(parsed.get("identification_status", "UNKNOWN")).upper()
            status = (
                IdentificationStatus[status_str]
                if status_str in IdentificationStatus.__members__
                else IdentificationStatus.UNKNOWN
            )
            confidence = float(parsed.get("confidence", 0.5))
            reasons = [str(r) for r in parsed.get("uncertainty_reasons", [])]

            return (
                RecognizedProduct(
                    product_id=parsed.get("product_id"),
                    name=parsed.get("name") or "Unknown Product",
                    brand=parsed.get("brand"),
                    category=parsed.get("category"),
                    confidence=max(0.0, min(1.0, confidence)),
                    visual_evidence=str(parsed.get("visual_evidence", "")),
                ),
                status,
                reasons,
            )
    except Exception as exc:
        return (
            RecognizedProduct(
                product_id=None,
                name="Unknown Product",
                brand=None,
                category=None,
                confidence=0.0,
                visual_evidence="Vision model request failed or returned unparseable output.",
            ),
            IdentificationStatus.UNKNOWN,
            [f"Gemma 4 vision recognition error: {exc}"],
        )


async def chat_with_candy_keeper(
    user_message: str,
    current_profile: DietaryProfile,
) -> tuple[str, list[str]]:
    """Process a user chat message with Gemma 4 and extract any dietary restrictions."""
    rule_extracted = extract_restrictions_from_text(user_message)

    if not settings.GEMINI_API_KEY:
        all_active = list(
            dict.fromkeys(current_profile.parsed_restrictions + rule_extracted)
        )
        active_desc = ", ".join(all_active) if all_active else "no specific curses yet"
        reply = (
            f"Ah, mortal! The Candy Keeper hears your decree! "
            f"Your forbidden list now guards against: {active_desc}. "
            f"Hold a candy wrapper before your camera to see if it is Candy or Curse!"
        )
        return reply, rule_extracted

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.GEMMA_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    )
    prompt = (
        f"{CHAT_SYSTEM_PROMPT}\n\n"
        f"Current restrictions: {current_profile.parsed_restrictions}\n"
        f"User message: {user_message}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 400},
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            text_out = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = _extract_json_object(text_out)
            reply = str(parsed.get("reply") or "The Candy Keeper notes your words!")
            model_extracted = [
                str(r).strip().lower().replace(" ", "_")
                for r in parsed.get("extracted_restrictions", [])
                if str(r).strip()
            ]
            combined = list(dict.fromkeys(rule_extracted + model_extracted))
            return reply, combined
    except Exception:
        all_active = list(
            dict.fromkeys(current_profile.parsed_restrictions + rule_extracted)
        )
        active_desc = ", ".join(all_active) if all_active else "none yet"
        return (
            f"The spirits flickered, but I recorded your restrictions ({active_desc})! "
            f"Scan a candy wrapper whenever you are ready.",
            rule_extracted,
        )
