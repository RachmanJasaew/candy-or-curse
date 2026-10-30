# Candy or Curse? — Shared API Contract (`v1.0.0`)

> **CRITICAL RULE FOR BOTH TEAMS:**
> This contract is frozen for MVP implementation. Neither Team A nor Team B may rename fields or change endpoint paths without updating this document, `frontend/src/types/api.ts`, and `backend/app/models/schemas.py` in a coordinated PR.

---

## 1. Core Principles & Safety Guarantees

1. **Never Claim "Allergy-Safe":** Neither the backend classifier nor Gemma 4 may ever state that a product is *"100% safe"* or *"definitively allergy-safe."* Manufacturing lines change without notice.
2. **Three-Tier Classification (`ClassificationStatus`):**
   - `GREEN` — **No Known Conflicting Ingredients:** Product is matched in our verified database (`VERIFIED_DATABASE`) with high confidence, and none of its verified ingredients/allergens conflict with the user's active dietary restrictions. Includes standard package verification reminder.
   - `RED` — **Verified Conflict Detected (CURSE!):** Product is matched in our verified database and contains one or more verified ingredients, allergens, or dietary violations (e.g., pork gelatin for vegan/halal, peanuts for peanut allergy).
   - `YELLOW` — **Insufficient or Uncertain Information (CAUTION!):** Product could not be confidently recognized by Gemma 4 (`UNKNOWN` or `AMBIGUOUS`), OR the recognized product is not in our verified ingredient database (`NONE`), OR user restrictions are ambiguous. **Gemma 4 must NEVER invent or guess ingredient lists.**
3. **Server-Side Keys Only:** `GEMINI_API_KEY` and `ELEVENLABS_API_KEY` live exclusively in `backend/.env`. The frontend communicates only with `/api/*`.
4. **HTTPS for Mobile Camera:** Mobile browsers block `navigator.mediaDevices.getUserMedia()` on insecure `http://` origins (except `localhost`). The QR code must point to an HTTPS URL (Lovable preview URL, Cloudflare Tunnel, or ngrok).

---

## 2. Shared Data Models

### `DietaryProfile`
```json
{
  "allergies": ["peanuts", "tree_nuts"],
  "dietary_preferences": ["vegan", "no_gelatin"],
  "raw_notes": "I am vegan and severely allergic to peanuts.",
  "parsed_restrictions": ["peanuts", "tree_nuts", "vegan", "no_gelatin", "dairy", "eggs", "honey"]
}
```

### `RecognizedProduct`
```json
{
  "product_id": "haribo-goldbears",
  "name": "Haribo Goldbears (Goldbären)",
  "brand": "Haribo",
  "category": "gummy_candy",
  "confidence": 0.94,
  "visual_evidence": "Gold wrapper with red HARIBO logo and cartoon bear; gummy bear shapes visible."
}
```

### `ScanResult` (Returned by `POST /api/sessions/{id}/scan`)
```json
{
  "scan_id": "scan_9f8e7d6c",
  "session_id": "sess_a1b2c3d4",
  "timestamp": "2026-10-30T16:00:00Z",
  "recognized_product": {
    "product_id": "haribo-goldbears",
    "name": "Haribo Goldbears (Goldbären)",
    "brand": "Haribo",
    "category": "gummy_candy",
    "confidence": 0.94,
    "visual_evidence": "Gold bag with red HARIBO lettering and bear mascot."
  },
  "identification_status": "IDENTIFIED",
  "ingredient_source": "VERIFIED_DATABASE",
  "classification": "RED",
  "headline": "CURSED! Contains Pork Gelatin",
  "conflicting_ingredients": [
    "Gelatin (Pork-derived)"
  ],
  "verified_ingredients": [
    "Glucose syrup",
    "Sugar",
    "Gelatin (Pork-derived)",
    "Dextrose",
    "Fruit juice from concentrate (apple, strawberry, raspberry, orange, lemon, pineapple)",
    "Citric acid",
    "Fruit and plant concentrates",
    "Carnauba wax",
    "Beeswax"
  ],
  "allergen_warnings": [
    "May contain traces of milk and wheat"
  ],
  "explanation": "Beware, mortal! Haribo Goldbears contain pork-derived gelatin and beeswax, which conflict with your vegan and gelatin-free restrictions.",
  "keeper_spoken_summary": "A dark curse lies within this golden pouch! Haribo Goldbears contain pork gelatin and beeswax—forbidden for vegans!",
  "uncertainty": {
    "is_uncertain": false,
    "confidence_score": 0.94,
    "reasons": []
  },
  "safety_disclaimer": "Classification is based on our verified reference database. Formulations vary by region and batch—always read the physical package label before consuming."
}
```

---

## 3. Endpoint Specifications

### 3.1 `POST /api/sessions`
Creates a new session (optionally seeded with initial dietary restrictions) and returns the session object including the mobile scan URL path for QR code rendering.

**Request Body (`CreateSessionRequest`):**
```json
{
  "initial_message": "I am vegan and allergic to peanuts",
  "allergies": ["peanuts"],
  "dietary_preferences": ["vegan", "no_gelatin"]
}
```
*(All fields are optional; an empty `{}` creates a fresh session that can be updated via chat.)*

**Response `201 Created` (`SessionResponse`):**
```json
{
  "session_id": "sess_a1b2c3d4",
  "created_at": "2026-10-30T16:00:00Z",
  "mobile_scan_path": "/scan/sess_a1b2c3d4",
  "mobile_scan_url": "https://your-lovable-or-tunnel-url.lovable.app/scan/sess_a1b2c3d4",
  "dietary_profile": {
    "allergies": ["peanuts"],
    "dietary_preferences": ["vegan", "no_gelatin"],
    "raw_notes": "I am vegan and allergic to peanuts",
    "parsed_restrictions": ["peanuts", "vegan", "no_gelatin", "gelatin", "dairy", "milk", "eggs", "honey"]
  },
  "chat_history": [
    {
      "role": "assistant",
      "content": "Welcome to the Crypt of Candies! I am The Candy Keeper. I have recorded your restrictions: Vegan, No Gelatin, and Peanut Allergy. Scan the QR code with your phone to inspect your Halloween loot!",
      "timestamp": "2026-10-30T16:00:00Z"
    }
  ],
  "scan_history": [],
  "latest_scan": null
}
```

---

### 3.2 `GET /api/sessions/{id}`
Retrieves the current session state, including any updates made via mobile scanning or chat.
- **Desktop client polls this endpoint every 2–3 seconds** (or on focus) to automatically display mobile scan results in real time.
- **Mobile client calls this on mount** to display the active user's dietary restrictions badge.

**Response `200 OK`:** Same schema as `SessionResponse` above.
**Response `404 Not Found`:** `{"detail": "Session not found"}`

---

### 3.3 `POST /api/sessions/{id}/chat`
Sends a text message (typed or transcribed from voice) to "The Candy Keeper" (Gemma 4).
Gemma 4 responds in character **and** extracts any new dietary restrictions to update `session.dietary_profile`.

**Request Body (`ChatRequest`):**
```json
{
  "message": "Also I cannot eat anything with gluten or soy."
}
```

**Response `200 OK` (`ChatResponse`):**
```json
{
  "session_id": "sess_a1b2c3d4",
  "reply": "Ah, gluten and soy shall not pass my lantern's gaze! I have added gluten and soy to your forbidden list. Show me a wrapper when you dare!",
  "updated_dietary_profile": {
    "allergies": ["peanuts", "gluten", "soy"],
    "dietary_preferences": ["vegan", "no_gelatin"],
    "raw_notes": "I am vegan and allergic to peanuts | Also I cannot eat anything with gluten or soy.",
    "parsed_restrictions": ["peanuts", "vegan", "no_gelatin", "gelatin", "dairy", "milk", "eggs", "honey", "gluten", "wheat", "soy"]
  },
  "extracted_new_restrictions": ["gluten", "soy"]
}
```

---

### 3.4 `POST /api/sessions/{id}/scan`
Uploads a captured candy image from the mobile camera (or desktop file picker), identifies the product via Gemma 4 Vision, looks up verified ingredients, and classifies against the session's `dietary_profile`.

Supports **either**:
1. **`multipart/form-data`** with an `image` file field (and optional `demo_product_hint` string field for offline testing), **OR**
2. **`application/json`** with `image_base64` (`data:image/jpeg;base64,...` or raw base64) and optional `mime_type` (`image/jpeg`, `image/png`, `image/webp`).

**Request Option A (`multipart/form-data`):**
- `image`: File (`image/jpeg`, `image/png`, `image/webp`)

**Request Option B (`application/json` - `ScanBase64Request`):**
```json
{
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
  "mime_type": "image/jpeg"
}
```

**Response `200 OK` (`ScanResult`):**
Returns the full `ScanResult` object (see Section 2) and appends it to `session.scan_history` and `session.latest_scan`.

#### Example `GREEN` Classification:
- `classification`: `"GREEN"`
- `identification_status`: `"IDENTIFIED"`
- `ingredient_source`: `"VERIFIED_DATABASE"`
- `conflicting_ingredients`: `[]`
- `headline`: `"CANDY! No Known Conflicting Ingredients"`

#### Example `RED` Classification:
- `classification`: `"RED"`
- `identification_status`: `"IDENTIFIED"`
- `ingredient_source`: `"VERIFIED_DATABASE"`
- `conflicting_ingredients`: `["Peanuts", "Milkfat", "Lactose"]`
- `headline`: `"CURSED! Contains Peanuts, Milkfat, Lactose"`

#### Example `YELLOW` Classification:
- `classification`: `"YELLOW"`
- `identification_status`: `"UNKNOWN"` (or `"AMBIGUOUS"`, or `"IDENTIFIED"` when `ingredient_source` is `"NONE"`)
- `ingredient_source`: `"NONE"`
- `conflicting_ingredients`: `[]`
- `headline`: `"UNCERTAIN! Unverified Product or Unclear Image"`
- `uncertainty`:
  ```json
  {
    "is_uncertain": true,
    "confidence_score": 0.42,
    "reasons": [
      "Product wrapper text is partially obscured or not in the verified 15-product database.",
      "Never consume an unverified product when managing allergies or strict dietary needs."
    ]
  }
  ```

---

### 3.5 `POST /api/voice/transcribe`
Transcribes user microphone audio into text using ElevenLabs Speech-to-Text (`scribe_v1`).

**Request (`multipart/form-data`):**
- `audio`: Audio file blob (`audio/webm`, `audio/mp4`, `audio/wav`, `audio/mpeg`)
- `language_code`: Optional ISO code (e.g., `"en"`, `"de"`)

**Response `200 OK` (`TranscribeResponse`):**
```json
{
  "text": "I am allergic to peanuts and I don't eat gelatin.",
  "language_code": "en",
  "provider": "elevenlabs_scribe_v1"
}
```

---

### 3.6 `POST /api/voice/synthesize`
Generates spooky voice audio for "The Candy Keeper" using ElevenLabs Text-to-Speech (`eleven_flash_v2_5`).

**Request Body (`SynthesizeRequest`):**
```json
{
  "text": "Beware! That Snickers bar harbors peanuts and milk—a perilous curse for you!",
  "voice_id": "JBFqnCBsd6RMkjVDRZzb"
}
```

**Response `200 OK` (`SynthesizeResponse`):**
```json
{
  "audio_base64": "//uQxAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAACAAABIADA...",
  "mime_type": "audio/mpeg",
  "provider": "elevenlabs_flash_v2_5"
}
```
*(Returning base64 JSON makes it trivial for React/Lovable to play immediately via `new Audio("data:audio/mpeg;base64," + res.audio_base64).play()` without blob URL CORS headaches, and allows clean mock fallback when offline!)*
