# Team B Implementation & Operations Guide (Gemma 4 + FastAPI + ElevenLabs)

This guide covers everything **Developer B1 (Gemma 4 & Vision)** and **Developer B2 (FastAPI & Classification)** need to run, test, and expose the backend for mobile QR scanning.

---

## 1. Quick Start (Local Setup in 60 Seconds)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy environment variables
cp ../.env.example .env
# Edit .env to add GEMINI_API_KEY and ELEVENLABS_API_KEY

# Run automated test suite (works even BEFORE adding API keys!)
pytest -v

# Start FastAPI server with hot reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive Swagger docs are automatically available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/api/health`
- **Verified Catalog:** `http://localhost:8000/api/products`

---

## 2. Verified API Models & Endpoints (Gemma 4 & ElevenLabs)

### 2.1 Gemma 4 Multimodal Vision & Chat (Developer B1)
- **Supported Model IDs in Google AI Studio (`generativelanguage.googleapis.com/v1beta`):**
  - `gemma-4-26b-a4b-it` *(Default — Mixture-of-Experts 26B Instruction-Tuned with native multimodal vision, fast latency for hackathon demos)*
  - `gemma-4-31b-it` *(Dense 31B Instruction-Tuned with native multimodal vision)*
- **Where implemented:** [`backend/app/services/gemma_service.py`](../backend/app/services/gemma_service.py)
- **How Vision Recognition Works (`recognize_candy_image`):**
  1. Receives raw image bytes (`image/jpeg`, `image/png`, `image/webp`) from `POST /api/sessions/{id}/scan`.
  2. Sends the image inline (`inline_data`) along with `VISION_SYSTEM_PROMPT` containing our 15-product catalog summary and visual cues.
  3. Parses structured JSON containing `product_id`, `name`, `brand`, `confidence`, `identification_status` (`IDENTIFIED` | `AMBIGUOUS` | `UNKNOWN`), `visual_evidence`, and `uncertainty_reasons`.
  4. **Anti-Hallucination Rule:** Gemma 4 never outputs ingredient lists. If confidence is `< 0.60` or `product_id` is not in `backend/app/data/products.json`, the deterministic classifier automatically assigns `YELLOW`.

### 2.2 ElevenLabs Speech-to-Text & Text-to-Speech (Developer B2 / A2)
- **Speech-to-Text (`POST /api/voice/transcribe`):**
  - Calls `POST https://api.elevenlabs.io/v1/speech-to-text` with header `xi-api-key: $ELEVENLABS_API_KEY` and `model_id="scribe_v1"`.
- **Text-to-Speech (`POST /api/voice/synthesize`):**
  - Calls `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}` with header `xi-api-key: $ELEVENLABS_API_KEY` and `model_id="eleven_flash_v2_5"` (ultra-low latency for real-time voice agents).
- **Graceful Fallback:** If `ELEVENLABS_API_KEY` is empty, both endpoints return valid mock responses so frontend testing never blocks.

---

## 3. Exposing FastAPI & Frontend Over HTTPS for Smartphone QR Scanning

> **CRITICAL:** Smartphones cannot access `http://localhost:8000`, and mobile Safari/Chrome block camera access (`getUserMedia`) on non-HTTPS URLs!

Use **Cloudflare Quick Tunnels** (free, no account needed) or **ngrok**:

```bash
# Terminal 1: Expose FastAPI Backend (port 8000) over HTTPS
npx cloudflared tunnel --url http://localhost:8000
# Copy the generated https://xxxx.trycloudflare.com URL into frontend/.env as VITE_API_BASE_URL

# Terminal 2: If running Vite locally instead of Lovable's hosted *.lovable.app URL:
npx cloudflared tunnel --url http://localhost:5173
# Copy that https://yyyy.trycloudflare.com URL into backend/.env as PUBLIC_FRONTEND_URL
```
*(If Team A is hosting the frontend on Lovable's preview URL `https://<project>.lovable.app`, set `PUBLIC_FRONTEND_URL=https://<project>.lovable.app` in `backend/.env` and only tunnel port 8000!)*
