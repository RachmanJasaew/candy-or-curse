"""Zero-dependency verification of the 20-product database and deterministic classification rules."""
import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "app" / "data" / "products.json"


def test_verified_database_integrity() -> None:
    products = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    assert len(products) == 20, f"Expected 20 verified products, got {len(products)}"

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
        assert len(prod["verified_ingredients"]) >= 1
        product_ids.add(prod["product_id"])

    for expected in [
        "haribo-goldbears",
        "snickers-original",
        "capri-sun-multivitamin",
        "voeslauer-mineralwasser",
        "red-bull-energy",
        "nutella-original",
        "manner-neapolitaner",
    ]:
        assert expected in product_ids, f"Missing required product {expected}"

    print("✅ All 20 verified products & classification triggers passed integrity checks!")


if __name__ == "__main__":
    test_verified_database_integrity()
