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
    assert "recommended_alternatives" in data["features"]

    cat_resp = client.get("/api/products")
    assert cat_resp.status_code == 200
    assert cat_resp.json()["count"] == 15


def test_session_creation_with_halal_and_allergies() -> None:
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
    # Must recommend compatible alternatives (e.g. Sour Patch Kids / Skittles)
    assert len(result["recommended_alternatives"]) >= 1
    alt_ids = [a["product_id"] for a in result["recommended_alternatives"]]
    assert "haribo-goldbears" not in alt_ids


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


def test_direct_ingredient_list_input_classification() -> None:
    session_id = client.post(
        "/api/sessions",
        json={"initial_message": "I want halal and no gelatin"},
    ).json()["session_id"]

    # 1. Ingredient list with pork gelatin -> RED + alternatives
    bad_resp = client.post(
        f"/api/sessions/{session_id}/scan",
        json={
            "ingredient_text_override": "Sugar, Glucose Syrup, Pork Gelatin, Citric Acid",
        },
    )
    assert bad_resp.status_code == 200
    bad_data = bad_resp.json()
    assert bad_data["classification"] == "RED"
    assert bad_data["ingredient_source"] == "USER_TEXT_INPUT"
    assert len(bad_data["recommended_alternatives"]) >= 1

    # 2. Clean water bottle ingredient list -> GREEN
    good_resp = client.post(
        f"/api/sessions/{session_id}/scan",
        json={
            "ingredient_text_override": "Carbonated Water, Natural Lemon Flavor, Citric Acid",
        },
    )
    assert good_resp.status_code == 200
    good_data = good_resp.json()
    assert good_data["classification"] == "GREEN"
    assert good_data["ingredient_source"] == "USER_TEXT_INPUT"
