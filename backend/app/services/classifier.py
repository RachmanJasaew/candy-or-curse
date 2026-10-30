"""Verified product lookup, OCR/text ingredient analyzer, alternative recommender, and deterministic classifier.

SAFETY POLICY:
- Never describe any product as "allergy-safe" or "100% safe".
- GREEN  = Verified product (or clear ingredient list) + zero conflicting ingredients for active restrictions.
- RED    = At least one conflicting ingredient or allergen warning detected -> includes recommended alternatives!
- YELLOW = Front of unknown product ("Okay, turn it around. Let me see the ingredients!"), blurry photo, or insufficient data.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Optional
import uuid

from app.models.schemas import (
    AlternativeProduct,
    ClassificationStatus,
    DietaryProfile,
    IdentificationStatus,
    IngredientSource,
    RecognizedProduct,
    ScanResult,
    UncertaintyInfo,
)

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "products.json"

SYNONYM_MAP: dict[str, list[str]] = {
    "eat_everything": ["eat everything", "eat_everything", "no restrictions", "anything", "alles essen"],
    "vegan": ["vegan", "plant-based", "plant based", "no animal products"],
    "vegetarian": ["vegetarian", "veggie", "meat-free"],
    "no_gelatin": ["no gelatin", "no_gelatin", "gelatin-free", "gelatin free", "avoid gelatin", "gelatine", "gelatin"],
    "pork": ["pork", "pork-free", "no pork", "swine", "pig", "schwein"],
    "halal": ["halal"],
    "kosher": ["kosher"],
    "peanuts": ["peanut", "peanuts", "groundnut", "arachis", "erdnuss", "erdnüsse"],
    "tree_nuts": ["tree nut", "tree nuts", "tree_nuts", "almond", "walnut", "cashew", "pecan", "pistachio"],
    "hazelnuts": ["hazelnut", "hazelnuts", "filbert", "haselnuss"],
    "nuts": ["nut", "nuts", "nut allergy", "allergic to nuts", "nüsse"],
    "milk": ["milk", "cow's milk", "cows milk", "milk protein", "whey", "casein", "butterfat", "skim milk", "milch"],
    "dairy": ["dairy", "dairy-free", "dairy free", "no dairy"],
    "lactose": ["lactose", "lactose intolerant", "lactose-free", "laktose"],
    "eggs": ["egg", "eggs", "egg white", "albumin", "ei", "eier"],
    "soy": ["soy", "soya", "soybean", "soy lecithin", "soja"],
    "wheat": ["wheat", "wheat flour", "weizen"],
    "gluten": ["gluten", "gluten-free", "gluten free", "celiac", "coeliac", "barley"],
    "fructose": ["fructose", "fructose intolerance"],
    "sugar_free": ["sugar-free", "sugar free", "no sugar", "diabetic", "zuckerfrei"],
}

# Ingredient keywords used when checking OCR or user-typed ingredient lists directly
RAW_INGREDIENT_CONFLICT_KEYWORDS: dict[str, list[str]] = {
    "vegan": ["gelatin", "gelatine", "milk", "whey", "lactose", "casein", "butter", "cream", "egg", "albumin", "honey", "beeswax", "carmine", "shellac", "pork", "beef", "yoghurt", "yogurt"],
    "vegetarian": ["gelatin", "gelatine", "pork", "beef", "lard", "tallow", "carmine"],
    "no_gelatin": ["gelatin", "gelatine"],
    "gelatin": ["gelatin", "gelatine"],
    "pork": ["pork", "swine", "gelatin", "gelatine", "lard", "bacon"],
    "halal": ["pork", "swine", "gelatin", "gelatine", "lard", "alcohol", "ethanol", "rum", "wine", "beer", "liqueur", "carmine"],
    "kosher": ["pork", "swine", "gelatin", "gelatine", "lard", "shellfish"],
    "peanuts": ["peanut", "peanuts", "groundnut", "arachis"],
    "tree_nuts": ["hazelnut", "almond", "walnut", "cashew", "pecan", "pistachio", "macadamia", "brazil nut", "tree nut"],
    "hazelnuts": ["hazelnut", "hazelnuts", "filbert"],
    "nuts": ["peanut", "hazelnut", "almond", "walnut", "cashew", "pecan", "pistachio", "nut"],
    "milk": ["milk", "whey", "lactose", "casein", "butter", "cream", "yoghurt", "yogurt", "dairy"],
    "dairy": ["milk", "whey", "lactose", "casein", "butter", "cream", "yoghurt", "yogurt", "dairy"],
    "lactose": ["lactose", "milk", "whey", "cream", "butter", "yoghurt", "yogurt"],
    "eggs": ["egg", "eggs", "albumin", "lysozyme"],
    "soy": ["soy", "soya", "soybean"],
    "wheat": ["wheat", "spelt", "semolina", "durum"],
    "gluten": ["wheat", "barley", "rye", "malt", "gluten", "spelt", "triticale"],
    "fructose": ["fructose", "high fructose corn syrup", "fruit juice", "sugar", "sucrose", "honey", "agave"],
    "sugar_free": ["sugar", "sucrose", "glucose syrup", "corn syrup", "dextrose", "fructose", "invert sugar", "maltose", "honey"],
}


def load_products() -> list[dict[str, Any]]:
    """Load the verified candy product database."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


PRODUCTS_DB: list[dict[str, Any]] = load_products()


def extract_restrictions_from_text(text: str) -> list[str]:
    """Extract canonical restriction tags from natural-language text."""
    if not text:
        return []
    lowered = text.lower()
    matched: list[str] = []
    for canonical, phrases in SYNONYM_MAP.items():
        for phrase in phrases:
            if phrase in lowered:
                matched.append(canonical)
                break
    return list(dict.fromkeys(matched))


def build_dietary_profile(
    allergies: Optional[list[str]] = None,
    dietary_preferences: Optional[list[str]] = None,
    raw_notes: str = "",
) -> DietaryProfile:
    """Normalize explicit allergies, preferences, and free-text notes into a DietaryProfile."""
    allergies_clean = [a.strip().lower() for a in (allergies or []) if a.strip()]
    prefs_clean = [p.strip().lower() for p in (dietary_preferences or []) if p.strip()]

    combined_text = " ".join(allergies_clean + prefs_clean + ([raw_notes] if raw_notes else []))
    parsed = extract_restrictions_from_text(combined_text)

    for token in allergies_clean + prefs_clean:
        norm = token.replace(" ", "_")
        if norm not in parsed:
            parsed.append(norm)

    # If user explicitly chose "eat_everything" and listed no other restrictions, keep only eat_everything
    if "eat_everything" in parsed and len(parsed) > 1:
        parsed = [r for r in parsed if r != "eat_everything"]

    if "vegan" in parsed:
        for implied in ["no_gelatin", "dairy", "milk", "eggs"]:
            if implied not in parsed:
                parsed.append(implied)

    if "halal" in parsed:
        for implied in ["pork", "no_gelatin"]:
            if implied not in parsed:
                parsed.append(implied)

    return DietaryProfile(
        allergies=allergies_clean,
        dietary_preferences=prefs_clean,
        raw_notes=raw_notes.strip(),
        parsed_restrictions=list(dict.fromkeys(parsed)),
    )


def find_verified_product(query_id_or_name: Optional[str]) -> Optional[dict[str, Any]]:
    """Match a Gemma-identified product ID or name against the verified products.json database."""
    if not query_id_or_name:
        return None
    q = query_id_or_name.strip().lower()
    if not q or q in {"unknown", "unknown product", "none", "unidentified"}:
        return None

    for prod in PRODUCTS_DB:
        if prod["product_id"].lower() == q or prod["name"].lower() == q:
            return prod
        if q in [alias.lower() for alias in prod.get("aliases", [])]:
            return prod

    for prod in PRODUCTS_DB:
        for alias in prod.get("aliases", []):
            alias_l = alias.lower()
            if alias_l in q or q in alias_l:
                return prod

    return None


def _get_product_conflicts(prod: dict[str, Any], restrictions: list[str]) -> list[str]:
    """Return list of conflicting ingredients for a single catalog product entry."""
    active_restrictions = [r for r in restrictions if r != "eat_everything"]
    if not active_restrictions:
        return []

    conflicts: list[str] = []
    triggers: dict[str, list[str]] = prod.get("conflict_triggers", {})
    verified_ingredients: list[str] = prod.get("verified_ingredients", [])
    allergen_warnings: list[str] = prod.get("allergen_warnings", [])
    flags: dict[str, bool] = prod.get("dietary_flags", {})

    for restriction in active_restrictions:
        if restriction in triggers:
            conflicts.extend(triggers[restriction])
        if restriction == "vegan" and not flags.get("vegan", False):
            if not triggers.get("vegan"):
                conflicts.append("Non-vegan formulation")
        if restriction == "vegetarian" and not flags.get("vegetarian", False):
            if not triggers.get("vegetarian"):
                conflicts.append("Contains animal-derived gelatin")
        if restriction in {"no_gelatin", "gelatin"} and flags.get("contains_gelatin", False):
            conflicts.append("Gelatin (Pork/Beef-derived)")
        if restriction in {"pork", "halal"} and flags.get("contains_pork", False):
            conflicts.append("Pork-derived gelatin")
        if restriction == "kosher" and not flags.get("kosher_friendly", True):
            conflicts.append("Non-kosher gelatin")
        if restriction in {"gluten", "gluten_free"} and not flags.get("gluten_free", True):
            if not triggers.get("gluten"):
                conflicts.append("Gluten-containing grain")

        term = restriction.replace("_", " ").lower()
        if len(term) >= 3 and term not in {"vegan", "vegetarian", "halal", "kosher", "no gelatin"}:
            for ing in verified_ingredients + allergen_warnings:
                if term in ing.lower():
                    conflicts.append(ing)

    return list(dict.fromkeys(conflicts))


def find_recommended_alternatives(
    exclude_product_id: Optional[str],
    preferred_category: Optional[str],
    dietary_profile: DietaryProfile,
    max_results: int = 3,
) -> list[AlternativeProduct]:
    """Find similar products from our verified database that have ZERO conflicts with the user's profile."""
    same_category: list[AlternativeProduct] = []
    other_category: list[AlternativeProduct] = []

    active_tags = [r for r in dietary_profile.parsed_restrictions if r != "eat_everything"]
    reason_suffix = (
        f"Compatible with your preferences ({', '.join(active_tags[:4])})"
        if active_tags
        else "No conflicting ingredients in verified database"
    )

    for prod in PRODUCTS_DB:
        if prod["product_id"] == exclude_product_id:
            continue
        conflicts = _get_product_conflicts(prod, dietary_profile.parsed_restrictions)
        if conflicts:
            continue

        alt = AlternativeProduct(
            product_id=prod["product_id"],
            name=prod["name"],
            brand=prod["brand"],
            category=prod["category"],
            reason=reason_suffix,
        )
        if preferred_category and prod.get("category") == preferred_category:
            same_category.append(alt)
        else:
            other_category.append(alt)

    return (same_category + other_category)[:max_results]


def _classify_raw_ingredient_list(
    raw_ingredients: list[str],
    restrictions: list[str],
) -> list[str]:
    """Check OCR-extracted or user-typed ingredient list against active restrictions."""
    active_restrictions = [r for r in restrictions if r != "eat_everything"]
    if not active_restrictions:
        return []

    conflicts: list[str] = []
    for restriction in active_restrictions:
        keywords = RAW_INGREDIENT_CONFLICT_KEYWORDS.get(
            restriction, [restriction.replace("_", " ").lower()]
        )
        for ing in raw_ingredients:
            ing_lower = ing.lower()
            for kw in keywords:
                if kw in ing_lower:
                    conflicts.append(f"{ing} (matches '{restriction}')")
                    break
    return list(dict.fromkeys(conflicts))


def classify_product_for_session(
    session_id: str,
    recognized: RecognizedProduct,
    identification_status: IdentificationStatus,
    dietary_profile: DietaryProfile,
    uncertainty_reasons: Optional[list[str]] = None,
    ocr_or_typed_ingredients: Optional[list[str]] = None,
    ingredient_source_override: Optional[IngredientSource] = None,
) -> ScanResult:
    """Deterministically classify a recognized food/candy or ingredient list against the user's DietaryProfile."""
    scan_id = f"scan_{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    reasons = list(uncertainty_reasons or [])

    # CASE 1: User provided explicit ingredient text OR Gemma read the back-of-pack ingredient list via OCR!
    cleaned_custom_ingredients = [
        i.strip() for i in (ocr_or_typed_ingredients or []) if i and i.strip()
    ]
    if cleaned_custom_ingredients:
        source = ingredient_source_override or IngredientSource.PACKAGE_OCR
        conflicts = _classify_raw_ingredient_list(
            cleaned_custom_ingredients, dietary_profile.parsed_restrictions
        )
        if conflicts:
            alts = find_recommended_alternatives(
                exclude_product_id=recognized.product_id,
                preferred_category=recognized.category,
                dietary_profile=dietary_profile,
            )
            alt_names = ", ".join(a.name for a in alts[:2])
            alt_spoken = f" Instead, I recommend trying {alt_names}!" if alt_names else ""
            conflict_str = ", ".join(conflicts)
            return ScanResult(
                scan_id=scan_id,
                session_id=session_id,
                timestamp=now_iso,
                recognized_product=recognized,
                identification_status=IdentificationStatus.IDENTIFIED,
                ingredient_source=source,
                classification=ClassificationStatus.RED,
                headline=f"NOT RECOMMENDED! Conflicts found on label",
                conflicting_ingredients=conflicts,
                verified_ingredients=cleaned_custom_ingredients,
                allergen_warnings=[],
                recommended_alternatives=alts,
                needs_ingredient_photo=False,
                agent_guidance_prompt=None,
                explanation=(
                    f"Based on the ingredient list provided for {recognized.name}, "
                    f"it contains conflicting ingredients: {conflict_str}."
                ),
                keeper_spoken_summary=(
                    f"Hold on! Reading those ingredients for {recognized.name}, "
                    f"it is not recommended for you because of {conflict_str}.{alt_spoken}"
                ),
                uncertainty=UncertaintyInfo(
                    is_uncertain=False,
                    confidence_score=max(0.85, recognized.confidence),
                    reasons=[],
                ),
            )

        return ScanResult(
            scan_id=scan_id,
            session_id=session_id,
            timestamp=now_iso,
            recognized_product=recognized,
            identification_status=IdentificationStatus.IDENTIFIED,
            ingredient_source=source,
            classification=ClassificationStatus.GREEN,
            headline="COMPATIBLE! No Conflicts Found in Ingredient List",
            conflicting_ingredients=[],
            verified_ingredients=cleaned_custom_ingredients,
            allergen_warnings=[],
            recommended_alternatives=[],
            needs_ingredient_photo=False,
            agent_guidance_prompt=None,
            explanation=(
                f"No conflicting ingredients were detected in the provided ingredient list for "
                f"{recognized.name} against your preferences. Always double-check physical allergen declarations."
            ),
            keeper_spoken_summary=(
                f"Thanks for showing me the ingredients! I checked the list for {recognized.name} "
                f"and found no conflicts with your preferences."
            ),
            uncertainty=UncertaintyInfo(
                is_uncertain=False,
                confidence_score=max(0.85, recognized.confidence),
                reasons=[],
            ),
        )

    # CASE 2: Lookup in our 15-product verified database
    verified_entry = find_verified_product(
        recognized.product_id or recognized.name
    )

    # CASE 3: Front of an unknown product (e.g. water bottle or snack not in DB) -> Ask user to turn it around!
    if (
        identification_status == IdentificationStatus.NEEDS_INGREDIENT_LABEL
        or (verified_entry is None and identification_status == IdentificationStatus.IDENTIFIED)
    ):
        prod_label = (
            recognized.name
            if recognized.name and recognized.name != "Unknown Product"
            else "this product"
        )
        guidance = f"Okay, I see {prod_label}. Turn it around—let me see the ingredient list on the back!"
        reasons.append(
            f"Front of '{prod_label}' detected, but exact ingredients are not in the pre-verified database."
        )
        reasons.append(
            "Turn the product around to show the nutrition/ingredient label, or paste the ingredient list below."
        )
        return ScanResult(
            scan_id=scan_id,
            session_id=session_id,
            timestamp=now_iso,
            recognized_product=recognized,
            identification_status=IdentificationStatus.NEEDS_INGREDIENT_LABEL,
            ingredient_source=IngredientSource.NONE,
            classification=ClassificationStatus.YELLOW,
            headline="TURN IT AROUND! Show Me the Ingredient List",
            conflicting_ingredients=[],
            verified_ingredients=[],
            allergen_warnings=[],
            recommended_alternatives=[],
            needs_ingredient_photo=True,
            agent_guidance_prompt=guidance,
            explanation=(
                f"I see the front of {prod_label}, but to check your preferences accurately, "
                f"turn it around so I can read the ingredient list on the back (or type the ingredients in)."
            ),
            keeper_spoken_summary=guidance,
            uncertainty=UncertaintyInfo(
                is_uncertain=True,
                confidence_score=recognized.confidence,
                reasons=reasons,
            ),
        )

    # CASE 4: Blurry or completely unrecognized image
    if (
        identification_status != IdentificationStatus.IDENTIFIED
        or recognized.confidence < 0.60
        or verified_entry is None
    ):
        if recognized.confidence < 0.60:
            reasons.append(
                f"Visual recognition confidence ({recognized.confidence:.0%}) is below the 60% verification threshold."
            )
        if not reasons:
            reasons.append("Product could not be clearly identified from the camera frame.")

        guidance = "Hold the package steady or turn it around so I can read the ingredient list!"
        explanation = (
            f"Caution! I cannot verify the exact ingredients for '{recognized.name}' yet. "
            f"{' '.join(reasons)} Turn the package around to show the ingredient list."
        )
        return ScanResult(
            scan_id=scan_id,
            session_id=session_id,
            timestamp=now_iso,
            recognized_product=recognized,
            identification_status=identification_status,
            ingredient_source=IngredientSource.NONE,
            classification=ClassificationStatus.YELLOW,
            headline="UNCERTAIN! Show Ingredient Label or Hold Steady",
            conflicting_ingredients=[],
            verified_ingredients=[],
            allergen_warnings=[],
            recommended_alternatives=[],
            needs_ingredient_photo=True,
            agent_guidance_prompt=guidance,
            explanation=explanation,
            keeper_spoken_summary=guidance,
            uncertainty=UncertaintyInfo(
                is_uncertain=True,
                confidence_score=recognized.confidence,
                reasons=reasons,
            ),
        )

    # CASE 5: Matched in our Verified 15-Product Database
    canonical_product = RecognizedProduct(
        product_id=verified_entry["product_id"],
        name=verified_entry["name"],
        brand=verified_entry.get("brand"),
        category=verified_entry.get("category"),
        confidence=recognized.confidence,
        visual_evidence=recognized.visual_evidence or verified_entry.get("visual_cues", ""),
    )

    verified_ingredients: list[str] = verified_entry.get("verified_ingredients", [])
    allergen_warnings: list[str] = verified_entry.get("allergen_warnings", [])
    deduped_conflicts = _get_product_conflicts(
        verified_entry, dietary_profile.parsed_restrictions
    )

    if deduped_conflicts:
        alts = find_recommended_alternatives(
            exclude_product_id=canonical_product.product_id,
            preferred_category=canonical_product.category,
            dietary_profile=dietary_profile,
        )
        alt_names = ", ".join(a.name for a in alts[:2])
        alt_text = f" Recommended alternatives for you: {alt_names}." if alt_names else ""
        alt_spoken = f" Instead, try {alt_names}, which fit your preferences!" if alt_names else ""

        conflict_str = ", ".join(deduped_conflicts)
        explanation = (
            f"CURSED / NOT RECOMMENDED! {canonical_product.name} contains verified conflicting ingredients "
            f"for your dietary profile: {conflict_str}.{alt_text}"
        )
        spoken = (
            f"Back away from the wrapper! {canonical_product.name} is not recommended for you "
            f"because it contains {conflict_str}.{alt_spoken}"
        )
        return ScanResult(
            scan_id=scan_id,
            session_id=session_id,
            timestamp=now_iso,
            recognized_product=canonical_product,
            identification_status=IdentificationStatus.IDENTIFIED,
            ingredient_source=IngredientSource.VERIFIED_DATABASE,
            classification=ClassificationStatus.RED,
            headline=f"CURSED! Contains {', '.join(deduped_conflicts[:2])}",
            conflicting_ingredients=deduped_conflicts,
            verified_ingredients=verified_ingredients,
            allergen_warnings=allergen_warnings,
            recommended_alternatives=alts,
            needs_ingredient_photo=False,
            agent_guidance_prompt=None,
            explanation=explanation,
            keeper_spoken_summary=spoken,
            uncertainty=UncertaintyInfo(
                is_uncertain=False,
                confidence_score=canonical_product.confidence,
                reasons=[],
            ),
        )

    # GREEN classification (never claim "allergy-safe")
    active_list = (
        ", ".join(dietary_profile.parsed_restrictions)
        if dietary_profile.parsed_restrictions
        else "eat everything / no active restrictions"
    )
    explanation = (
        f"No known conflicting ingredients were found in our verified database record for "
        f"{canonical_product.name} against your active preferences ({active_list}). "
        f"Note: Always verify the physical package label, as regional recipes and factory lines vary."
    )
    spoken = (
        f"Good news! Our verified scroll shows no known conflicting ingredients "
        f"in {canonical_product.name} for your preferences, though you should always check the wrapper!"
    )
    return ScanResult(
        scan_id=scan_id,
        session_id=session_id,
        timestamp=now_iso,
        recognized_product=canonical_product,
        identification_status=IdentificationStatus.IDENTIFIED,
        ingredient_source=IngredientSource.VERIFIED_DATABASE,
        classification=ClassificationStatus.GREEN,
        headline="CANDY! No Known Conflicting Ingredients",
        conflicting_ingredients=[],
        verified_ingredients=verified_ingredients,
        allergen_warnings=allergen_warnings,
        recommended_alternatives=[],
        needs_ingredient_photo=False,
        agent_guidance_prompt=None,
        explanation=explanation,
        keeper_spoken_summary=spoken,
        uncertainty=UncertaintyInfo(
            is_uncertain=False,
            confidence_score=canonical_product.confidence,
            reasons=[],
        ),
    )
