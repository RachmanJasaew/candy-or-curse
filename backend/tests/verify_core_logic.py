"""Zero-dependency verification of the 15-product database and deterministic classification rules."""
import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "app" / "data" / "products.json"


def test_verified_database_integrity() -> None:
    products = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    assert len(products) == 15, f"Expected 15 verified products, got {len(products)}"

    required_keys = {
        "product_id",
        "name",
        "brand",
        "category",
        "aliases",
        "visual_cues",
        "verified_ingredients",
        "allergens",
        "allergen_warnings",
        "dietary_flags",
        "conflict_triggers",
    }
    product_ids = set()
    for prod in products:
        missing = required_keys - set(prod.keys())
        assert not missing, f"Product {prod.get('product_id')} missing keys: {missing}"
        assert len(prod["verified_ingredients"]) >= 3
        product_ids.add(prod["product_id"])

    # Verify required hackathon products are present
    for expected in ["haribo-goldbears", "snickers-original", "capri-sun-multivitamin"]:
        assert expected in product_ids, f"Missing required product {expected}"

    # Verify Haribo triggers vegan & no_gelatin conflict
    haribo = next(p for p in products if p["product_id"] == "haribo-goldbears")
    assert haribo["dietary_flags"]["contains_gelatin"] is True
    assert haribo["dietary_flags"]["vegan"] is False
    assert "Gelatin (Pork-derived)" in haribo["conflict_triggers"]["vegan"]

    # Verify Snickers triggers peanut & dairy conflict
    snickers = next(p for p in products if p["product_id"] == "snickers-original")
    assert "peanuts" in snickers["allergens"]
    assert "Peanuts" in snickers["conflict_triggers"]["peanuts"]

    # Verify Capri-Sun is vegan and peanut-free
    capri = next(p for p in products if p["product_id"] == "capri-sun-multivitamin")
    assert capri["dietary_flags"]["vegan"] is True
    assert capri["allergens"] == []

    print("✅ All 15 verified products & classification triggers passed integrity checks!")


if __name__ == "__main__":
    test_verified_database_integrity()
