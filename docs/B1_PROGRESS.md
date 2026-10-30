# B1 implementation and verification

Branch: `feature/gemma-vision`. Prepared for publication and review; main is not modified by this branch.
The shared API models, catalog, classifier and endpoints are unchanged by B1. Integration adds only Vite environment type declarations to the frontend.

## Implemented

- Google Gemma REST integration with credentials in headers and sanitized diagnostics.
- 90-second read timeout, one retry on transient failures, and a 120-second bound per generation (up to two generations for OCR).
- Unknown products supported through ingredient-label coaching; visible names preserved.
- Exact catalog IDs receive canonical metadata. Non-catalog names cannot become an identified catalog match through fuzzy lookup.
- No-key, malformed, blocked, truncated, nonfinite-confidence, and low-confidence responses fail to an uncertain result.
- Thinking parts are excluded from JSON parsing.
- OCR is accepted only for a complete, legible list with IDENTIFIED and confidence >= 0.60, followed by a separate visual verification of the proposed list. Rejection or failure of verification suppresses the OCR.
- OCR transcribes a single ingredient paragraph verbatim with its English translation, retaining parentheses and percentages. The service packages it into the existing ingredient-list field; shared API models are unchanged. This avoids model-generated list splitting that caused duplicated subingredients.
- Detected duplicate language translations or repeated grouped ingredients reject the OCR instead of attempting to repair it silently.
- Candy Keeper chat uses separate system instructions, supported restriction tags, and a local fallback when the provider fails or returns a detected unqualified safety claim.
- Live chat uses model-extracted tags rather than blindly merging substring matches that can contradict explicit negation.

## Evidence

- 24 offline backend tests pass. Includes all 15 catalog-ID mappings, malformed/uncertain outputs, retry behavior, thought/truncation parsing, translated German gluten/vegan conflicts, chat extraction, and duplicate OCR rejection.
- Live unknown-front photo: S Budget energy drink returned NEEDS_INGREDIENT_LABEL at 0.98 with no ingredients.
- Live catalog image: official Haribo Goldbears packshot returned haribo-goldbears, IDENTIFIED at 0.99, and no generated ingredients. Source: https://www.haribo.com/en-us/products/goldbears . This was a clean manufacturer packshot, not a phone-photo robustness benchmark.
- Live chat returned a Candy Keeper reply and extracted vegan and gluten from the authorized test message.
- Live label OCR returned printed ingredients with English translations, but merged languages and repeated vitamin entries. Added deterministic rejection checks for those faults. A subsequent label request timed out. An image-first request then returned an incomplete list despite claiming completeness, motivating the separate verifier. Therefore reliable, accurate real-label OCR is NOT yet signed off.
- Google has intermittently returned HTTP 500 and timeouts, including on generic prompts and the official SDK. One successful call does not establish service reliability.

## Run checks

From `backend`:

```sh
GEMINI_API_KEY='' .venv/bin/python -m pytest -q
```

From the repository root, test live generic generation without personal data:

```sh
backend/.venv/bin/python scripts/check_gemma.py
```

The checker returns a nonzero exit code when live generation fails; a fallback is not a pass.

## Remaining acceptance and integration work

B1 core functionality is implemented. Accurate label transcription and broader phone-photo robustness must be assessed separately from code/test completion.

B2 integration risks to resolve before relying on dietary verdicts:
- The classifier currently treats any nonempty OCR list as sufficient for a verdict and can issue GREEN. Confidence and completeness reported by a model do not prove allergy safety or vegan status.
- English translations enable keyword matches but cannot establish the origin of ambiguous additives or missing cross-contact declarations.
- Session storage reparses raw notes with a substring parser, which can reintroduce restrictions denied by a user even when B1 extracts them correctly. Removal of restrictions is not supported by the additive session API.
- OCR scans can take up to 240 seconds because they include a second visual check. The client should allow only one scan in flight and avoid queuing live camera frames.

No API keys or user photos are included in these artifacts.

Live verifier check: the known-incomplete transcription of the user's label
(missing caffeine, inositol, and the complete vitamin group) returned `complete=false`.
This verifies a real rejection case; it is not a guarantee that every OCR error
will be detected. Both passes use the same model, so correlated errors remain possible.

Final full-photo verification run: completed in 111 seconds and returned NEEDS_INGREDIENT_LABEL with no OCR because the verifier could not confirm the list. A focused German crop also exposed duplicated vitamins, correctly rejected. Paragraph transcription was added after these checks.

Final paragraph-OCR crop test completed in 102 seconds. The independent check
could not confirm the proposed list; the service returned NEEDS_INGREDIENT_LABEL
with empty OCR. This is a correct guardrail rejection, not an accurate-OCR pass.
A clearer, preferably flat single-language ingredient label is needed for the
remaining positive real-label acceptance test. The existing curved-can photo must
not be used as evidence of a successful dietary classification.


## Online-label positive acceptance test

Source: https://www.hersheyland.com/products/reeses-oreo-milk-chocolate-peanut-butter-cups-1-4-oz.html
Back image: https://s7d1.scene7.com/is/image/hersheyprodcloud/0_34000_45813_4_701_45812_004_Item_Back_A?fmt=png&hei=2400&qlt=100

The high-resolution full-package image completed in 108 seconds with IDENTIFIED,
a full ingredient paragraph, and the peanuts/milk/soy declaration. The independent
visual verifier accepted it. Manual comparison with the image confirmed that the
ingredient groups, the final TBHQ/citric-acid entries, and all three declared allergens
were included. This provides the missing positive real-label OCR test. It does not
establish accuracy for all products or reliability under repeated requests.

The same call assigned the Oreo variant a generic Reese's catalog ID. Fixed that
boundary: label scans now clear catalog identity and use photographed ingredients
only. A rejected label cannot fall back to a catalog recipe. Added regressions for
both cases. The visible product name remains available. A separate cropped-image
attempt returned HTTP 500 and UNKNOWN, reinforcing the documented provider issue.

B1's core acceptance paths now have live evidence: catalog recognition, unknown-front
coaching, positive label OCR with verification, rejection of incomplete OCR, and
conversational restriction extraction. Wider phone-photo testing and B2 integration
risks above remain. Earlier negative OCR results in this document are retained as
limitations and motivation for the final safeguards, rather than positive evidence.


## Integration with A1/B2 main

Rebased onto origin/main at 8092dab, including A1 UI and B2's expanded 20-product
catalog, bilingual classifier, persistent sessions, and backend-served UI. The A2
voice-qr branch was still at the original scaffold when fetched. Vision catalog
counts now follow the database dynamically.

Validation on the combined branch:
- 26 backend tests pass with live API keys disabled.
- TypeScript and Vite production build pass. Added src/vite-env.d.ts to resolve
  missing ImportMeta.env declarations in the existing frontend.
- Deterministic integration smoke passed: desktop/mobile HTML, session creation,
  RED and YELLOW scan responses, and latest-scan session polling.
- Production build output was directed to a temporary directory so the existing
  backend-served frontend/dist/index.html was preserved.

These checks do not replace a real phone/camera/QR/ElevenLabs end-to-end rehearsal.
Live provider testing and broader photo testing remain for the later test session.
