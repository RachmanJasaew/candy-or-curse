"""Automated tests for the Candy or Curse FastAPI Backend (Developer B2)."""
import base64
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
DUMMY_IMAGE_B64 = base64.b64encode(b"fake_jpeg_bytes_for_testing").decode("utf-8")


def test_health_and_catalog() -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["verified_products_count"] == 15

    cat_resp = client.get("/api/products")
    assert cat_resp.status_code == 200
    assert cat_resp.json()["count"] == 15


def test_session_creation_and_retrieval() -> None:
    resp = client.post(
        "/api/sessions",
        json={
            "initial_message": "I am vegan and allergic to peanuts",
            "allergies": ["peanuts"],
            "dietary_preferences": ["vegan", "no_gelatin"],
        },
    )
    assert resp.status_code == 201
    session = resp.json()
    session_id = session["session_id"]
    assert session_id.startswith("sess_")
    assert session["mobile_scan_path"] == f"/scan/{session_id}"
    assert "peanuts" in session["dietary_profile"]["parsed_restrictions"]
    assert "vegan" in session["dietary_profile"]["parsed_restrictions"]
    assert "no_gelatin" in session["dietary_profile"]["parsed_restrictions"]

    get_resp = client.get(f"/api/sessions/{session_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["session_id"] == session_id


def test_chat_updates_dietary_restrictions() -> None:
    session_id = client.post("/api/sessions", json={}).json()["session_id"]
    chat_resp = client.post(
        f"/api/sessions/{session_id}/chat",
        json={"message": "I have a severe peanut allergy and I avoid gluten."},
    )
    assert chat_resp.status_code == 200
    body = chat_resp.json()
    assert "peanuts" in body["updated_dietary_profile"]["parsed_restrictions"]
    assert "gluten" in body["updated_dietary_profile"]["parsed_restrictions"]


def test_scan_red_classification_for_haribo_vegan() -> None:
    session_id = client.post(
        "/api/sessions",
        json={"initial_message": "I am vegan and avoid gelatin"},
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
    assert result["identification_status"] == "IDENTIFIED"
    assert result["ingredient_source"] == "VERIFIED_DATABASE"
    assert any("Gelatin" in item for item in result["conflicting_ingredients"])
    assert "allergy-safe" not in result["explanation"].lower()


def test_scan_green_classification_for_capri_sun_vegan_peanut_allergy() -> None:
    session_id = client.post(
        "/api/sessions",
        json={"initial_message": "I am vegan and allergic to peanuts"},
    ).json()["session_id"]

    scan_resp = client.post(
        f"/api/sessions/{session_id}/scan",
        json={
            "image_base64": DUMMY_IMAGE_B64,
            "mime_type": "image/jpeg",
            "demo_product_hint": "capri-sun-multivitamin",
        },
    )
    assert scan_resp.status_code == 200
    result = scan_resp.json()
    assert result["classification"] == "GREEN"
    assert result["identification_status"] == "IDENTIFIED"
    assert result["ingredient_source"] == "VERIFIED_DATABASE"
    assert result["conflicting_ingredients"] == []
    # Must NEVER describe a product as definitively allergy-safe
    assert "allergy-safe" not in result["explanation"].lower()
    assert "100% safe" not in result["explanation"].lower()


def test_scan_yellow_classification_for_unknown_or_unverified_product() -> None:
    session_id = client.post(
        "/api/sessions",
        json={"initial_message": "Allergic to tree nuts"},
    ).json()["session_id"]

    # 1. Blurry / unknown image
    unknown_resp = client.post(
        f"/api/sessions/{session_id}/scan",
        json={
            "image_base64": DUMMY_IMAGE_B64,
            "demo_product_hint": "unknown",
        },
    )
    assert unknown_resp.status_code == 200
    u_res = unknown_resp.json()
    assert u_res["classification"] == "YELLOW"
    assert u_res["ingredient_source"] == "NONE"
    assert u_res["uncertainty"]["is_uncertain"] is True

    # 2. Named product NOT in our verified 15-product DB
    unverified_resp = client.post(
        f"/api/sessions/{session_id}/scan",
        json={
            "image_base64": DUMMY_IMAGE_B64,
            "demo_product_hint": "Mystery Homemade Fudge",
        },
    )
    assert unverified_resp.status_code == 200
    unv_res = unverified_resp.json()
    assert unv_res["classification"] == "YELLOW"
    assert unv_res["ingredient_source"] == "NONE"
    assert unv_res["verified_ingredients"] == []


def test_voice_endpoints_mock_fallback() -> None:
    synth_resp = client.post(
        "/api/voice/synthesize",
        json={"text": "Welcome to the Crypt of Candies!"},
    )
    assert synth_resp.status_code == 200
    assert synth_resp.json()["mime_type"] == "audio/mpeg"
    assert len(synth_resp.json()["audio_base64"]) > 10

    transcribe_resp = client.post(
        "/api/voice/transcribe",
        files={"audio": ("speech.webm", b"dummy_webm_audio_bytes", "audio/webm")},
    )
    assert transcribe_resp.status_code == 200
    assert len(transcribe_resp.json()["text"]) > 0
