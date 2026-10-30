# Copy-Paste Lovable Prompt & GitHub Sync Guide (Team A — Developer A1)

## Copy-Paste Prompt for Lovable

Copy everything inside the code block below and paste it into **Lovable**:

```text
Build "Candy or Curse?", an interactive AI Food & Halloween Candy Scanner web application with ElevenLabs conversational voice coaching and two main routes:

1. DESKTOP STATION & ONBOARDING (`/`):
- Dark Halloween/modern theme with quick onboarding preference chips when you first open the app:
  - "☪️ Halal", "🌱 Vegan", "🥗 Vegetarian", "🥜 Peanut Allergy", "🌾 Gluten-Free", "🥛 Lactose-Free", and "🍽️ Eat Everything" (plus free-text and microphone voice input for any custom allergy or ingredient you don't want to eat).
- Conversational AI Agent ("The Candy Keeper") connected to ElevenLabs Speech-to-Text (`POST /api/voice/transcribe`) and Text-to-Speech (`POST /api/voice/synthesize`) + `POST /api/sessions/{id}/chat`.
- QR Code Connection Card:
  - Renders a QR code pointing to `${window.location.origin}/scan/${session_id}`.
  - Polls `GET /api/sessions/{id}` every 2.5 seconds so live scans from the user's phone appear on the laptop screen automatically.

2. MOBILE LIVE SCANNER (`/scan/:sessionId`):
- Connected to the same `sessionId` and shows the user's active preferences at the top.
- Supports 3 ways to scan ANY food product or drink:
  1. **Front-of-Pack OR Back-of-Pack Camera Snapshot** (`facingMode: "environment"` + file/camera upload fallback).
  2. **🔴 Continuous Live Stream Mode**: Periodically captures video frames every 4 seconds while filming a product and talks back naturally via ElevenLabs! If the user films the front of an unfamiliar product (like a water bottle), the agent says: *"Okay, turn it around. Let me see the ingredients!"* (`needs_ingredient_photo: true`, `agent_guidance_prompt`).
  3. **📝 Direct Ingredient List Input**: A text input where users can paste or type an ingredient list for 100% accuracy (`ingredient_text_override`).
- Full-Card Classification Overlay (`GREEN` / `RED` / `YELLOW`) returned by `POST /api/sessions/{sessionId}/scan`:
  - `GREEN`: Recommended / Compatible with your preferences.
  - `RED`: Not Recommended — highlights `conflicting_ingredients` AND displays a **"✅ Recommended Similar Alternatives"** section (`recommended_alternatives`: list of `{ product_id, name, brand, category, reason }`) suggesting similar products that DO match the user's preferences!
  - `YELLOW`: Uncertain / Needs Ingredient Label — displays `agent_guidance_prompt` (e.g., *"Okay, turn it around. Let me see the ingredients!"*) and prompts the user to flip the package to the ingredient list.
```
