# Copy-Paste Lovable Prompt & GitHub Sync Guide (Team A — Developer A1)

## Important: How Lovable + GitHub Sync Works

1. **Lovable's GitHub Sync Behavior:**
   - Lovable cannot attach to a pre-existing populated repository during its initial project creation; when you connect a new Lovable project to GitHub, Lovable creates a repository and mirrors the repository root on `main`.
   - **Recommended Hackathon Workflow (Two Options):**
     - **Option 1 (Fastest — Sync Lovable into `frontend/`):** Create the UI in Lovable using the prompt below, connect Lovable to GitHub (e.g. `candy-or-curse-lovable`), and run `./scripts/sync_lovable.sh <lovable-repo-url>` to pull Lovable's generated UI directly into `frontend/` in our `candy-or-curse` monorepo!
     - **Option 2 (Drop Contract Files into Lovable):** Upload `docs/openapi.json`, `frontend/src/types/api.ts`, `frontend/src/mocks/mockData.ts`, and `frontend/src/api/client.ts` directly into your Lovable project so Lovable generates components against our exact API schemas from minute one.

---

## Copy-Paste Prompt for Lovable

Copy everything inside the code block below and paste it into **Lovable**:

```text
Build "Candy or Curse?", a spooky, high-polish Halloween AI Candy Scanner web application with two main routes:

1. DESKTOP STATION (`/`):
- Dark Gothic Halloween theme (deep midnight purple `#0c0714`, glowing jack-o'-lantern orange `#f97316`, potion emerald `#10b981`, blood curse crimson `#f43f5e`, and warning amber `#fbbf24`).
- Hero stage featuring our AI character "The Candy Keeper" (an animated/glowing spooky guardian of the trick-or-treat cauldron).
- Interactive Chat & Voice Panel where the user tells The Candy Keeper their dietary restrictions (e.g., "I am vegan, avoid gelatin, and have a peanut allergy"):
  - Text chat input + Send button.
  - "Speak to The Candy Keeper" microphone record button (records audio blob and sends to `POST /api/voice/transcribe`, then sends transcript to `POST /api/sessions/{id}/chat`, and plays spoken audio from `POST /api/voice/synthesize`).
  - Active Dietary Restrictions displayed as glowing pill badges (e.g. `peanuts`, `vegan`, `no_gelatin`, `gluten`).
- QR Code Connection Card:
  - Renders a scannable QR code pointing to `${window.location.origin}/scan/${session_id}`.
  - Polls `GET /api/sessions/{id}` every 2.5 seconds so whenever the user scans a candy on their smartphone, the latest scan verdict automatically pops up on the desktop screen too!

2. MOBILE SCANNER (`/scan/:sessionId`):
- Mobile-first vertical layout connected to the same `sessionId`.
- Shows the user's active dietary restriction badges at the top (fetched from `GET /api/sessions/{sessionId}`).
- Smartphone Camera Capture:
  - Live rear camera viewfinder (`navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })`) with a big glowing "Capture Candy Wrapper" button.
  - Native mobile camera/photo upload fallback (`<input type="file" accept="image/*" capture="environment" />`) so it always works on iOS Safari and Android Chrome.
  - Three quick-test demo buttons ("Green: Capri-Sun", "Red: Haribo", "Yellow: Mystery") that pass `demo_product_hint` for instant hackathon testing.
- Dramatic Full-Card Classification Overlay (`GREEN` / `RED` / `YELLOW`) returned by `POST /api/sessions/{sessionId}/scan`:
  - `GREEN`: Emerald glow — "CANDY! No Known Conflicting Ingredients"
  - `RED`: Crimson glow — "CURSED! Verified Conflicting Ingredient Detected" with a highlighted list of `conflicting_ingredients`.
  - `YELLOW`: Amber glow — "UNCERTAIN! Insufficient Product or Ingredient Data" with `uncertainty.reasons`.
  - Always display `recognized_product.name`, confidence percentage, `explanation`, and the mandatory `safety_disclaimer` (never claim a product is 100% allergy-safe).

3. STRICT API CONTRACT:
Use these exact endpoints and JSON field names (with a `VITE_USE_MOCK_API=true` toggle that returns mock GREEN/RED/YELLOW responses when the backend is offline):
- `POST /api/sessions` -> returns `{ session_id, mobile_scan_path, mobile_scan_url, dietary_profile, chat_history, scan_history, latest_scan }`
- `GET /api/sessions/{id}` -> returns `SessionResponse`
- `POST /api/sessions/{id}/chat` -> body `{ message }` -> returns `{ session_id, reply, updated_dietary_profile, extracted_new_restrictions }`
- `POST /api/sessions/{id}/scan` -> `multipart/form-data` (`image` file) or JSON `{ image_base64, mime_type, demo_product_hint }` -> returns `ScanResult` (`classification`: `"GREEN" | "RED" | "YELLOW"`, `identification_status`: `"IDENTIFIED" | "AMBIGUOUS" | "UNKNOWN"`, `ingredient_source`: `"VERIFIED_DATABASE" | "NONE"`, `headline`, `conflicting_ingredients`, `verified_ingredients`, `allergen_warnings`, `explanation`, `keeper_spoken_summary`, `uncertainty`, `safety_disclaimer`)
- `POST /api/voice/transcribe` -> `multipart/form-data` (`audio` file) -> returns `{ text, language_code, provider }`
- `POST /api/voice/synthesize` -> JSON `{ text, voice_id }` -> returns `{ audio_base64, mime_type, provider }`
```
