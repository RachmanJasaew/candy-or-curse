"""Comprehensive Automated Pytest Suite for Developer B2 (`feature/backend-classification`)."""
import base64
from fastapi.testclient import TestClient
from app.main import app
from app.services.session_store import SessionStore

client = TestClient(app)
DUMMY_IMAGE_B64 = base64.b64encode(b"fake_jpeg_bytes_for_testing").decode("utf-8")


def test_health_and_20_product_catalog() -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["verified_products_count"] == 20
    assert "recommended_alternatives" in data["features"]
    assert "session_disk_persistence" in data["features"]

    cat_resp = client.get("/api/products")
    assert cat_resp.status_code == 200
    assert cat_resp.json()["count"] == 20

    # Detail lookup by slug or alias
    manner_resp = client.get("/api/products/manner-neapolitaner")
    assert manner_resp.status_code == 200
    assert manner_resp.json()["brand"] == "Manner (Wien)"


def test_session_creation_persistence_and_preference_update() -> None:
    resp = client.post(
        "/api/sessions",
        json={
            "initial_message": "I want halal food and I am allergic to peanuts",
            "allergies": ["peanuts"],
            "dietary_preferences": ["halal"],
        },
    )
    assert resp.status_code == 201
    session = resp.json()
    session_id = session["session_id"]
    assert "halal" in session["dietary_profile"]["parsed_restrictions"]
    assert "peanuts" in session["dietary_profile"]["parsed_restrictions"]

    # Verify disk persistence across SessionStore instances
    reloaded_store = SessionStore()
    reloaded_session = reloaded_store.get_session(session_id)
    assert reloaded_session is not None
    assert reloaded_session.session_id == session_id

    # Update preferences via PUT /api/sessions/{id}/preferences
    put_resp = client.put(
        f"/api/sessions/{session_id}/preferences",
        json={
            "allergies": ["gluten"],
            "dietary_preferences": ["vegan"],
            "initial_message": "Switched to vegan and gluten-free",
        },
    )
    assert put_resp.status_code == 200
    updated = put_resp.json()
    assert "vegan" in updated["dietary_profile"]["parsed_restrictions"]
    assert "gluten" in updated["dietary_profile"]["parsed_restrictions"]


def test_scan_red_includes_recommended_alternatives() -> None:
    session_id = client.post(
        "/api/sessions",
        json={"initial_message": "I eat halal and avoid gelatin"},
    ).json()["session_id"]

    scan_resp = client.post(
        f"/api/sessions/{session_id}/scan",
        json={
            "image_base64": DUMMY_IMAGE_B64,
            "mime_type": "image/jpeg",
            "demo_product_hint": "haribo-goldbears",
        },
    )
    assert scan_resp.status_code == 200
    result = scan_resp.json()
    assert result["classification"] == "RED"
    assert any("Gelatin" in item for item in result["conflicting_ingredients"])
    assert len(result["recommended_alternatives"]) >= 1
    alt_ids = [a["product_id"] for a in result["recommended_alternatives"]]
    assert "haribo-goldbears" not in alt_ids
    assert "allergy-safe" not in result["explanation"].lower()


def test_water_bottle_front_asks_user_to_turn_around_for_ingredients() -> None:
    session_id = client.post(
        "/api/sessions",
        json={"initial_message": "I am vegan"},
    ).json()["session_id"]

    scan_resp = client.post(
        f"/api/sessions/{session_id}/scan",
        json={
            "image_base64": DUMMY_IMAGE_B64,
            "demo_product_hint": "water-bottle-front",
        },
    )
    assert scan_resp.status_code == 200
    res = scan_resp.json()
    assert res["classification"] == "YELLOW"
    assert res["identification_status"] == "NEEDS_INGREDIENT_LABEL"
    assert res["needs_ingredient_photo"] is True
    assert "turn it around" in (res["agent_guidance_prompt"] or "").lower()


def test_german_and_english_ingredient_list_input() -> None:
    session_id = client.post(
        "/api/sessions",
        json={"initial_message": "Ich esse halal und keine Erdnüsse"},
    ).json()["session_id"]

    # 1. German ingredient label with Schweinegelatine & Erdnüsse -> RED + alternatives
    bad_resp = client.post(
        f"/api/sessions/{session_id}/scan",
        json={
            "ingredient_text_override": "Zutaten: Glukosesirup, Zucker, Schweinegelatine, Erdnüsse, Citronensäure",
        },
    )
    assert bad_resp.status_code == 200
    bad_data = bad_resp.json()
    assert bad_data["classification"] == "RED"
    assert bad_data["ingredient_source"] == "USER_TEXT_INPUT"
    assert len(bad_data["conflicting_ingredients"]) >= 2
    assert len(bad_data["recommended_alternatives"]) >= 1

    # 2. Clean water bottle ingredient list -> GREEN
    good_resp = client.post(
        f"/api/sessions/{session_id}/scan",
        json={
            "ingredient_text_override": "Zutaten: Natürliches Mineralwasser, Kohlensäure, Zitronensaftkonzentrat",
        },
    )
    assert good_resp.status_code == 200
    good_data = good_resp.json()
    assert good_data["classification"] == "GREEN"
    assert good_data["ingredient_source"] == "USER_TEXT_INPUT"


def test_eat_everything_preference_allows_all_verified_products() -> None:
    session_id = client.post(
        "/api/sessions",
        json={"initial_message": "I eat everything"},
    ).json()["session_id"]

    scan_resp = client.post(
        f"/api/sessions/{session_id}/scan",
        json={
            "image_base64": DUMMY_IMAGE_B64,
            "demo_product_hint": "snickers-original",
        },
    )
    assert scan_resp.status_code == 200
    assert scan_resp.json()["classification"] == "GREEN"


def test_voice_endpoints_mock_fallback() -> None:
    synth_resp = client.post(
        "/api/voice/synthesize",
        json={"text": "Okay, turn it around. Let me see the ingredients!"},
    )
    assert synth_resp.status_code == 200
    assert synth_resp.json()["mime_type"] == "audio/mpeg"

    transcribe_resp = client.post(
        "/api/voice/transcribe",
        files={"audio": ("speech.webm", b"dummy_webm_audio_bytes", "audio/webm")},
    )
    assert transcribe_resp.status_code == 200
    assert len(transcribe_resp.json()["text"]) > 0
