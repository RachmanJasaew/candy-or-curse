"""B1 vision guardrails: model output must not bypass classification uncertainty."""
import asyncio
import json

from app.models.schemas import ClassificationStatus, DietaryProfile, IdentificationStatus
from app.services import gemma_service as vision
from app.services.classifier import classify_product_for_session


def run_scan(monkeypatch, response):
    monkeypatch.setattr(vision.settings, "GEMINI_API_KEY", "test-key")

    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": json.dumps(response)}]}}]}

    class Client:
        def __init__(self, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def post(self, url, **kwargs):
            assert kwargs["json"]["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "minimal"
            assert "test-key" not in url
            assert kwargs["headers"]["x-goog-api-key"] == "test-key"
            if any("Verify this proposed" in part.get("text", "")
                   for part in kwargs["json"]["contents"][0]["parts"]):
                class VerificationResponse(Response):
                    def json(self):
                        return {"candidates": [{"content": {"parts": [{"text": '{"complete":true}'}]}}]}
                return VerificationResponse()
            return Response()

    monkeypatch.setattr(vision.httpx, "AsyncClient", Client)
    return asyncio.run(vision.recognize_candy_image(b"image"))


def test_no_key_does_not_invent_product(monkeypatch):
    monkeypatch.setattr(vision.settings, "GEMINI_API_KEY", "")
    product, status, reasons, ingredients = asyncio.run(vision.recognize_candy_image(b"image"))
    assert status == IdentificationStatus.UNKNOWN
    assert product.product_id is None and ingredients == [] and reasons


def test_uncertain_model_output_cannot_be_classified_from_ocr(monkeypatch):
    product, status, reasons, ingredients = run_scan(monkeypatch, {
        "product_id": "haribo-goldbears", "name": "Haribo", "confidence": 0.2,
        "identification_status": "IDENTIFIED", "ingredient_list_complete": True,
        "ocr_ingredients": ["sugar"],
    })
    assert status == IdentificationStatus.AMBIGUOUS and not ingredients
    result = classify_product_for_session("test", product, status, DietaryProfile(), reasons, ingredients)
    assert result.classification == ClassificationStatus.YELLOW


def test_unknown_variant_does_not_fuzzy_match_catalog(monkeypatch):
    product, status, _, ingredients = run_scan(monkeypatch, {
        "product_id": "not-in-catalog", "name": "Snickers", "confidence": 0.9,
        "identification_status": "IDENTIFIED", "ocr_ingredients": ["sugar"],
    })
    assert product.product_id is None and product.name == "Snickers"
    assert status == IdentificationStatus.NEEDS_INGREDIENT_LABEL and not ingredients


def test_complete_label_transcription(monkeypatch):
    _, status, _, ingredients = run_scan(monkeypatch, {
        "confidence": 0.9, "identification_status": "IDENTIFIED",
        "ingredient_list_complete": True, "ocr_ingredients": ["sugar", "milk"],
    })
    assert status == IdentificationStatus.IDENTIFIED
    assert ingredients == ["sugar", "milk"]


def test_malformed_model_response_fails_closed(monkeypatch):
    product, status, reasons, ingredients = run_scan(monkeypatch, {
        "confidence": "not-a-number", "identification_status": "IDENTIFIED",
        "ingredient_list_complete": True, "ocr_ingredients": ["sugar"],
    })
    assert product.product_id is None
    assert status == IdentificationStatus.UNKNOWN and reasons and not ingredients


def test_known_catalog_identity_uses_canonical_metadata(monkeypatch):
    product, status, _, ingredients = run_scan(monkeypatch, {
        "product_id": "haribo-goldbears", "name": "invented name", "brand": "invented",
        "confidence": 0.95, "identification_status": "IDENTIFIED",
        "ocr_ingredients": [],
    })
    assert status == IdentificationStatus.IDENTIFIED
    assert product.brand == "Haribo" and product.name != "invented name"
    assert ingredients == []


def test_final_answer_excludes_thinking_parts():
    assert vision._response_text({'candidates': [{'finishReason': 'STOP', 'content': {
        'parts': [{'thought': True, 'text': 'internal reasoning'}, {'text': '{"ok":true}'}]
    }}]}) == '{"ok":true}'


def test_truncated_answer_is_rejected():
    import pytest
    with pytest.raises(ValueError):
        vision._response_text({'candidates': [{'finishReason': 'MAX_TOKENS',
            'content': {'parts': [{'text': '{"ocr_ingredients":["sugar"]}'}]}}]})


def test_chat_uses_supported_model_tags_without_substring_false_positives(monkeypatch):
    monkeypatch.setattr(vision.settings, 'GEMINI_API_KEY', 'test-key')
    async def generate(payload):
        assert 'systemInstruction' in payload
        return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': json.dumps({
            'reply': 'Show me the label.', 'extracted_restrictions': ['vegan', 'gluten', 'invented_tag']
        })}]}}]}
    monkeypatch.setattr(vision, '_generate', generate)
    reply, tags = asyncio.run(vision.chat_with_candy_keeper(
        'I am vegan, need gluten-free food, and have no peanut allergy.', DietaryProfile()))
    assert tags == ['vegan', 'gluten']
    assert reply == 'Show me the label.'


def test_all_catalog_ids_use_canonical_metadata(monkeypatch):
    for entry in vision.PRODUCTS_DB:
        product, status, _, ingredients = run_scan(monkeypatch, {
            'product_id': entry['product_id'], 'confidence': 0.95,
            'identification_status': 'IDENTIFIED', 'ocr_ingredients': []})
        assert product.name == entry['name'] and product.product_id == entry['product_id']
        assert status == IdentificationStatus.IDENTIFIED and ingredients == []


def test_translated_german_label_reaches_existing_conflict_checker(monkeypatch):
    from app.services.classifier import build_dietary_profile
    product, status, reasons, ingredients = run_scan(monkeypatch, {
        'confidence': 0.95, 'identification_status': 'IDENTIFIED',
        'ingredient_list_complete': True,
        'ocr_ingredients': ['Weizenmehl [wheat flour]', 'Milchpulver [milk powder]']})
    result = classify_product_for_session('test', product, status,
        build_dietary_profile(dietary_preferences=['vegan', 'gluten']), reasons, ingredients)
    assert result.classification == ClassificationStatus.RED
    assert any('gluten' in i for i in result.conflicting_ingredients)
    assert any('vegan' in i for i in result.conflicting_ingredients)


def test_provider_retries_only_transient_failure(monkeypatch):
    import httpx
    calls = []
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, **kwargs):
            calls.append(url)
            return httpx.Response(500 if len(calls) == 1 else 200,
                request=httpx.Request('POST', url), json={'candidates': []})
    monkeypatch.setattr(vision.httpx, 'AsyncClient', Client)
    assert asyncio.run(vision._generate({})) == {'candidates': []}
    assert len(calls) == 2


def test_duplicate_subingredients_are_not_classified(monkeypatch):
    product, status, reasons, ingredients = run_scan(monkeypatch, {
        'confidence': 0.95, 'identification_status': 'IDENTIFIED',
        'ingredient_list_complete': True,
        'ocr_ingredients': ['Vitamin B12 [Vitamin B12]',
                            'Vitamine (Niacin, Vitamin B12) [Vitamins (Niacin, Vitamin B12)]']})
    assert ingredients == [] and reasons
    assert status == IdentificationStatus.NEEDS_INGREDIENT_LABEL
    result = classify_product_for_session('test', product, status, DietaryProfile(), reasons, ingredients)
    assert result.classification == ClassificationStatus.YELLOW


def test_duplicate_languages_are_rejected(monkeypatch):
    _, status, reasons, ingredients = run_scan(monkeypatch, {
        'confidence': 0.95, 'identification_status': 'IDENTIFIED',
        'ingredient_list_complete': True,
        'ocr_ingredients': ['Wasser [Water]', 'Acqua [water]']})
    assert not ingredients and reasons
    assert status == IdentificationStatus.NEEDS_INGREDIENT_LABEL


def test_chat_drops_unqualified_safety_claim(monkeypatch):
    monkeypatch.setattr(vision.settings, 'GEMINI_API_KEY', 'test-key')
    async def generate(payload):
        return {'candidates': [{'content': {'parts': [{'text': json.dumps({
            'reply': 'This is 100% safe.', 'extracted_restrictions': []})}]}}]}
    monkeypatch.setattr(vision, '_generate', generate)
    reply, _ = asyncio.run(vision.chat_with_candy_keeper('Hello', DietaryProfile()))
    assert '100% safe' not in reply


def test_second_visual_check_rejects_incomplete_ocr(monkeypatch):
    monkeypatch.setattr(vision.settings, 'GEMINI_API_KEY', 'test-key')
    answers = iter([
        {'identification_status': 'IDENTIFIED', 'confidence': 0.95,
         'ingredient_list_complete': True, 'ocr_ingredients': ['water', 'sugar']},
        {'complete': False},
    ])
    async def generate(payload):
        return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
            {'text': json.dumps(next(answers))}]}}]}
    monkeypatch.setattr(vision, '_generate', generate)
    product, status, reasons, ingredients = asyncio.run(vision.recognize_candy_image(b'image'))
    assert not ingredients and reasons
    assert status == IdentificationStatus.NEEDS_INGREDIENT_LABEL
    result = classify_product_for_session('test', product, status, DietaryProfile(), reasons, ingredients)
    assert result.classification == ClassificationStatus.YELLOW


def test_verbatim_paragraph_preserves_groups_and_translation(monkeypatch):
    _, status, _, ingredients = run_scan(monkeypatch, {
        'confidence': 0.95, 'identification_status': 'IDENTIFIED',
        'ingredient_list_complete': True, 'ocr_ingredients': [],
        'ocr_original_text': 'Wasser, Vitamine (Niacin, Vitamin B12).',
        'ocr_english_text': 'Water, vitamins (niacin, vitamin B12).',
    })
    assert status == IdentificationStatus.IDENTIFIED
    assert ingredients == ['Wasser, Vitamine (Niacin, Vitamin B12). [Water, vitamins (niacin, vitamin B12).]']


def test_label_does_not_inherit_wrong_variant_catalog_identity(monkeypatch):
    product, status, _, ingredients = run_scan(monkeypatch, {
        'product_id': 'reeses-peanut-butter-cups', 'name': "Reese's Oreo cups",
        'confidence': 0.98, 'identification_status': 'IDENTIFIED',
        'ingredient_list_complete': True, 'ocr_ingredients': ['milk', 'peanuts'],
    })
    assert product.product_id is None and product.name == "Reese's Oreo cups"
    assert status == IdentificationStatus.IDENTIFIED and ingredients


def test_rejected_label_cannot_fall_back_to_catalog_recipe(monkeypatch):
    product, status, reasons, ingredients = run_scan(monkeypatch, {
        'product_id': 'haribo-goldbears', 'confidence': 0.95,
        'identification_status': 'IDENTIFIED', 'ingredient_list_complete': False,
        'ocr_ingredients': ['sugar'],
    })
    assert product.product_id is None and not ingredients
    result = classify_product_for_session('test', product, status, DietaryProfile(), reasons, ingredients)
    assert result.classification == ClassificationStatus.YELLOW
