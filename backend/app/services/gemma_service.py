"""Gemma 4 Vision and Conversational AI Service (Developer B1).

Uses Google AI Studio / Gemini API (`gemma-4-26b-a4b-it` or `gemma-4-31b-it`) for:
1. Multimodal Food/Candy Wrapper Recognition (Front of product OR Back-of-pack Ingredient Label OCR)
2. Conversational "Candy Keeper" Live Coaching ("Okay, turn it around. Let me see the ingredients.")

CRITICAL RULE:
Gemma 4 must NEVER invent or guess ingredient lists from the front of a package.
- If the front matches our 15-product verified catalog, return its `product_id`.
- If the front is an unknown product (like a water bottle or unfamiliar snack), set `identification_status` to `"NEEDS_INGREDIENT_LABEL"` so the agent asks the user to flip the product around.
- Only populate `ocr_ingredients` when the printed ingredient list on the back of the package is actually visible and legible in the photo!
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

VISION_SYSTEM_PROMPT = f"""You are the visual recognition and live camera coach engine for "Candy or Curse?".
Analyze the user's photo or video frame of ANY food product, beverage, or candy.

Known Verified Catalog:
{CATALOG_SUMMARY}

STRICT RULES:
1. NEVER invent or guess ingredient lists from a front label.
2. CASE A (Known Catalog Product): If the image clearly shows one of the 15 known catalog products, set "product_id" to that exact slug, "identification_status" to "IDENTIFIED", and "ocr_ingredients" to [].
3. CASE B (Back of Package / Visible Ingredient Label): If the image shows a printed Ingredient List on the back/side of ANY food product, read the visible printed ingredients into "ocr_ingredients" (list of strings) and set "identification_status" to "IDENTIFIED".
4. CASE C (Front of an Unknown Food/Beverage Product, e.g. a water bottle or unfamiliar snack): Set "product_id" to null, "name" to the visible product type/brand (e.g. "Sparkling Water Bottle"), "identification_status" to "NEEDS_INGREDIENT_LABEL", and "ocr_ingredients" to []. The voice agent will then tell the user: "Okay, turn it around. Let me see the ingredients!"
5. CASE D (Blurry / Empty Frame): Set "identification_status" to "UNKNOWN".
6. Respond ONLY with valid JSON matching this exact structure:
{{
  "product_id": "haribo-goldbears" | null,
  "name": "Haribo Goldbears (Goldbären)",
  "brand": "Haribo" | null,
  "category": "gummy_candy" | null,
  "confidence": 0.94,
  "identification_status": "IDENTIFIED" | "NEEDS_INGREDIENT_LABEL" | "AMBIGUOUS" | "UNKNOWN",
  "visual_evidence": "Brief description of what is visible in the frame.",
  "ocr_ingredients": [],
  "uncertainty_reasons": []
}}
"""

CHAT_SYSTEM_PROMPT = """You are "The Candy Keeper", a charismatic, natural-sounding AI food & Halloween candy coach.
Your job:
1. Converse naturally (2-3 sentences max) so it feels like a real conversation, not a robotic program.
2. Listen for any dietary preferences or restrictions: Halal, Kosher, Vegan, Vegetarian, Eat Everything, No Gelatin, or allergies (peanuts, tree nuts, milk/dairy/lactose, gluten/wheat, soy, eggs).
3. Remind the user they can film the front of any food product—or flip it around to show the ingredient list on the back!
4. NEVER claim any product is "100% allergy-safe" or invent ingredient lists.
5. Respond ONLY with valid JSON matching this exact structure:
{
  "reply": "Natural conversational response acknowledging their preferences and coaching them on scanning.",
  "extracted_restrictions": ["halal", "peanuts", "no_gelatin"]
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
) -> tuple[RecognizedProduct, IdentificationStatus, list[str], list[str]]:
    """Identify a packaged food/candy or read back-of-pack ingredients using Gemma 4 Vision.

    Returns: `(RecognizedProduct, IdentificationStatus, uncertainty_reasons, ocr_ingredients)`
    """
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
                [],
            )
        if hint in {"water-bottle-front", "turn-around", "unknown-front"}:
            return (
                RecognizedProduct(
                    product_id=None,
                    name="Flavored Water Bottle",
                    brand="Local Brand",
                    category="beverage",
                    confidence=0.88,
                    visual_evidence="Front of a plastic water bottle; ingredient list is on the back.",
                ),
                IdentificationStatus.NEEDS_INGREDIENT_LABEL,
                ["Front of bottle detected; flip around to read ingredients."],
                [],
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
                    [],
                )
        # Named product not in our verified DB -> triggers NEEDS_INGREDIENT_LABEL ("Turn it around!")
        return (
            RecognizedProduct(
                product_id=None,
                name=demo_product_hint,
                brand="Unverified Brand",
                category="food_product",
                confidence=0.82,
                visual_evidence=f"Front of {demo_product_hint} visible, but ingredient label not shown.",
            ),
            IdentificationStatus.NEEDS_INGREDIENT_LABEL,
            [f"'{demo_product_hint}' is not in the verified 15-product database."],
            [],
        )

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
            [],
        )

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
            "maxOutputTokens": 600,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            text_out = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = _extract_json_object(text_out)

            status_str = str(parsed.get("identification_status", "UNKNOWN")).upper()
            status = (
                IdentificationStatus[status_str]
                if status_str in IdentificationStatus.__members__
                else IdentificationStatus.UNKNOWN
            )
            confidence = float(parsed.get("confidence", 0.5))
            reasons = [str(r) for r in parsed.get("uncertainty_reasons", [])]
            ocr_ingredients = [
                str(i).strip()
                for i in parsed.get("ocr_ingredients", [])
                if str(i).strip()
            ]

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
                ocr_ingredients,
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
            [],
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
        active_desc = ", ".join(all_active) if all_active else "eat everything (no restrictions)"
        reply = (
            f"Got it! I have updated your profile to: {active_desc}. "
            f"Show me the front of any food product—or turn it around to show the ingredient list!"
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
            reply = str(parsed.get("reply") or "I've updated your dietary preferences!")
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
            f"I recorded your preferences ({active_desc})! "
            f"Hold any product or its ingredient list up to the camera whenever you're ready.",
            rule_extracted,
        )
