"""Verified product lookup and deterministic GREEN / RED / YELLOW ingredient classifier.

SAFETY POLICY:
- Never describe any product as "allergy-safe" or "100% safe".
- GREEN = Verified product in database + zero conflicting ingredients found for active restrictions.
- RED   = Verified product in database + at least one conflicting ingredient or allergen warning.
- YELLOW = Unknown/ambiguous product, confidence below threshold, or unverified ingredient source.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Optional
import uuid

from app.models.schemas import (
    ClassificationStatus,
    DietaryProfile,
    IdentificationStatus,
    IngredientSource,
    RecognizedProduct,
    ScanResult,
    UncertaintyInfo,
)

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "products.json"

# Canonical keyword synonyms mapping natural language phrases to canonical tags
SYNONYM_MAP: dict[str, list[str]] = {
    "vegan": ["vegan", "plant-based", "plant based", "no animal products"],
    "vegetarian": ["vegetarian", "veggie", "meat-free"],
    "no_gelatin": ["no gelatin", "no_gelatin", "gelatin-free", "gelatin free", "avoid gelatin", "gelatine", "gelatin"],
    "pork": ["pork", "pork-free", "no pork", "swine", "pig"],
    "halal": ["halal"],
    "kosher": ["kosher"],
    "peanuts": ["peanut", "peanuts", "groundnut", "arachis"],
    "tree_nuts": ["tree nut", "tree nuts", "tree_nuts", "almond", "walnut", "cashew", "pecan", "pistachio"],
    "hazelnuts": ["hazelnut", "hazelnuts", "filbert"],
    "nuts": ["nut", "nuts", "nut allergy", "allergic to nuts"],
    "milk": ["milk", "cow's milk", "cows milk", "milk protein", "whey", "casein", "butterfat", "skim milk"],
    "dairy": ["dairy", "dairy-free", "dairy free", "no dairy"],
    "lactose": ["lactose", "lactose intolerant", "lactose-free"],
    "eggs": ["egg", "eggs", "egg white", "albumin"],
    "soy": ["soy", "soya", "soybean", "soy lecithin"],
    "wheat": ["wheat", "wheat flour"],
    "gluten": ["gluten", "gluten-free", "gluten free", "celiac", "coeliac", "barley"],
    "fructose": ["fructose", "fructose intolerance"],
    "sugar_free": ["sugar-free", "sugar free", "no sugar", "diabetic"],
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

    # Also keep direct tokens provided in allergies/preferences
    for token in allergies_clean + prefs_clean:
        norm = token.replace(" ", "_")
        if norm not in parsed:
            parsed.append(norm)

    # Expand implied restrictions (e.g., vegan implies no_gelatin, dairy, milk, eggs)
    if "vegan" in parsed:
        for implied in ["no_gelatin", "dairy", "milk", "eggs"]:
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

    # 1. Exact product_id or name match
    for prod in PRODUCTS_DB:
        if prod["product_id"].lower() == q or prod["name"].lower() == q:
            return prod
        if q in [alias.lower() for alias in prod.get("aliases", [])]:
            return prod

    # 2. Substring match against aliases
    for prod in PRODUCTS_DB:
        for alias in prod.get("aliases", []):
            alias_l = alias.lower()
            if alias_l in q or q in alias_l:
                return prod

    return None


def classify_product_for_session(
    session_id: str,
    recognized: RecognizedProduct,
    identification_status: IdentificationStatus,
    dietary_profile: DietaryProfile,
    uncertainty_reasons: Optional[list[str]] = None,
) -> ScanResult:
    """Deterministically classify a recognized candy against the user's DietaryProfile."""
    scan_id = f"scan_{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    reasons = list(uncertainty_reasons or [])

    # Check if recognition is uncertain or unknown
    verified_entry = find_verified_product(
        recognized.product_id or recognized.name
    )

    if (
        identification_status != IdentificationStatus.IDENTIFIED
        or recognized.confidence < 0.60
        or verified_entry is None
    ):
        if verified_entry is None and identification_status == IdentificationStatus.IDENTIFIED:
            reasons.append(
                f"'{recognized.name}' is not in our verified 15-product ingredient database."
            )
        if recognized.confidence < 0.60:
            reasons.append(
                f"Visual recognition confidence ({recognized.confidence:.0%}) is below the 60% verification threshold."
            )
        if not reasons:
            reasons.append("Product could not be unambiguously identified from the photo.")

        explanation = (
            f"Caution, mortal! My crystal ball cannot verify the exact ingredients for "
            f"'{recognized.name}'. {' '.join(reasons)} "
            f"Please inspect the physical wrapper carefully."
        )
        spoken = (
            f"Proceed with caution! The mists obscure this treat. "
            f"I cannot verify the ingredients for {recognized.name}. Check the wrapper yourself!"
        )
        return ScanResult(
            scan_id=scan_id,
            session_id=session_id,
            timestamp=now_iso,
            recognized_product=recognized,
            identification_status=(
                identification_status
                if verified_entry is not None
                else (
                    IdentificationStatus.AMBIGUOUS
                    if recognized.name and recognized.name != "Unknown Product"
                    else IdentificationStatus.UNKNOWN
                )
            ),
            ingredient_source=IngredientSource.NONE,
            classification=ClassificationStatus.YELLOW,
            headline="UNCERTAIN! Insufficient Product or Ingredient Data",
            conflicting_ingredients=[],
            verified_ingredients=[],
            allergen_warnings=[],
            explanation=explanation,
            keeper_spoken_summary=spoken,
            uncertainty=UncertaintyInfo(
                is_uncertain=True,
                confidence_score=recognized.confidence,
                reasons=reasons,
            ),
        )

    # Canonicalize RecognizedProduct metadata from verified_entry
    canonical_product = RecognizedProduct(
        product_id=verified_entry["product_id"],
        name=verified_entry["name"],
        brand=verified_entry.get("brand"),
        category=verified_entry.get("category"),
        confidence=recognized.confidence,
        visual_evidence=recognized.visual_evidence or verified_entry.get("visual_cues", ""),
    )

    conflicts: list[str] = []
    triggers: dict[str, list[str]] = verified_entry.get("conflict_triggers", {})
    verified_ingredients: list[str] = verified_entry.get("verified_ingredients", [])
    allergen_warnings: list[str] = verified_entry.get("allergen_warnings", [])
    flags: dict[str, bool] = verified_entry.get("dietary_flags", {})

    for restriction in dietary_profile.parsed_restrictions:
        # 1. Explicit trigger map lookup
        if restriction in triggers:
            conflicts.extend(triggers[restriction])

        # 2. Dietary boolean flag check
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

        # 3. Substring search across verified ingredients & allergen warnings for custom allergens
        term = restriction.replace("_", " ").lower()
        if len(term) >= 3 and term not in {"vegan", "vegetarian", "halal", "kosher", "no gelatin"}:
            for ing in verified_ingredients + allergen_warnings:
                if term in ing.lower():
                    conflicts.append(ing)

    deduped_conflicts = list(dict.fromkeys(conflicts))

    if deduped_conflicts:
        conflict_str = ", ".join(deduped_conflicts)
        explanation = (
            f"CURSED! {canonical_product.name} contains verified conflicting ingredients "
            f"for your dietary profile: {conflict_str}."
        )
        spoken = (
            f"Back away from the wrapper! {canonical_product.name} is cursed for you! "
            f"It contains {conflict_str}."
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
        else "no active restrictions specified"
    )
    explanation = (
        f"No known conflicting ingredients were found in our verified database record for "
        f"{canonical_product.name} against your active restrictions ({active_list}). "
        f"Note: Always verify the physical package label, as regional recipes and factory lines vary."
    )
    spoken = (
        f"A sweet treat indeed! Our verified scroll shows no known conflicting ingredients "
        f"in {canonical_product.name} for your restrictions, though you should always check the wrapper!"
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
        explanation=explanation,
        keeper_spoken_summary=spoken,
        uncertainty=UncertaintyInfo(
            is_uncertain=False,
            confidence_score=canonical_product.confidence,
            reasons=[],
        ),
    )
