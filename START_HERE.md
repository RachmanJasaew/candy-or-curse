# 🚀 START HERE — Team Action Plan (Candy or Curse?)

Welcome to **Candy or Curse?**! Everything is already scaffolded and ready. Follow the steps below for your role.

---

## Step 1: Clone the Repository (Everyone)

```bash
git clone https://github.com/RachmanJasaew/candy-or-curse.git
cd candy-or-curse
```

---

## Step 2: What Each Developer Does Right Now

### 🎨 Developer A1 — Lovable & UI (Team A)
1. Switch to your branch:
   ```bash
   git checkout feature/frontend-ui
   ```
2. Open [`docs/LOVABLE_PROMPT.md`](docs/LOVABLE_PROMPT.md), copy the prompt, and paste it into **Lovable.dev** to generate/polish the visual interface (or edit [`frontend/src/pages/DesktopHome.tsx`](frontend/src/pages/DesktopHome.tsx), [`frontend/src/pages/MobileScanner.tsx`](frontend/src/pages/MobileScanner.tsx), and [`frontend/src/components/ClassificationOverlay.tsx`](frontend/src/components/ClassificationOverlay.tsx) directly).
3. **Your GitHub Issues:**
   - [Issue #1 — Desktop Landing & Chat UI](https://github.com/RachmanJasaew/candy-or-curse/issues/1)
   - [Issue #2 — Mobile Camera & Live Scanner View](https://github.com/RachmanJasaew/candy-or-curse/issues/2)
   - [Issue #3 — GREEN / RED / YELLOW Overlays & Alternatives](https://github.com/RachmanJasaew/candy-or-curse/issues/3)

---

### 🎙️ Developer A2 — ElevenLabs Voice & QR Sync (Team A)
1. Switch to your branch and start the frontend:
   ```bash
   git checkout feature/voice-qr
   cd frontend && cp ../.env.example .env
   npm install && npm run dev
   ```
2. Because `VITE_USE_MOCK_API=true` is enabled by default in `.env`, the entire frontend works immediately using realistic mock data (`GREEN`, `RED` with alternatives, and `YELLOW` *"Turn it around, let me see the ingredients!"*).
3. Test and refine microphone recording, ElevenLabs voice playback ([`frontend/src/services/voiceRecorder.ts`](frontend/src/services/voiceRecorder.ts)), and desktop-to-mobile QR polling ([`frontend/src/hooks/useSessionSync.ts`](frontend/src/hooks/useSessionSync.ts)).
4. **Your GitHub Issues:**
   - [Issue #4 — API Client, Mock Toggle & QR Session Polling](https://github.com/RachmanJasaew/candy-or-curse/issues/4)
   - [Issue #5 — ElevenLabs Speech-to-Text Microphone Integration](https://github.com/RachmanJasaew/candy-or-curse/issues/5)
   - [Issue #6 — ElevenLabs Text-to-Speech Playback](https://github.com/RachmanJasaew/candy-or-curse/issues/6)

---

### 👁️ Developer B1 — Gemma 4 Vision & Live Voice Coach (Team B)
1. Switch to your branch:
   ```bash
   git checkout feature/gemma-vision
   ```
2. Get a Google AI Studio API key (`GEMINI_API_KEY`) and put it in `backend/.env`.
3. Test [`backend/app/services/gemma_service.py`](backend/app/services/gemma_service.py) with real phone photos:
   - **Known product front** (Haribo, Snickers, Capri-Sun, etc.) $\rightarrow$ matches our verified database.
   - **Unknown product front** (e.g., a water bottle) $\rightarrow$ triggers `NEEDS_INGREDIENT_LABEL` so the agent says: *"Okay, turn it around. Let me see the ingredients!"*
   - **Back of package (Ingredient list)** $\rightarrow$ reads the printed ingredients via OCR (`ocr_ingredients`).
4. **Your GitHub Issues:**
   - [Issue #7 — Gemma 4 Multimodal Vision Recognition](https://github.com/RachmanJasaew/candy-or-curse/issues/7)
   - [Issue #8 — Anti-Hallucination & "Turn It Around" Coaching Guardrails](https://github.com/RachmanJasaew/candy-or-curse/issues/8)
   - [Issue #9 — Conversational Chat & Preference Extraction](https://github.com/RachmanJasaew/candy-or-curse/issues/9)

---

### ⚙️ Developer B2 — FastAPI Backend, Classifier & HTTPS Tunnel (Team B)
1. Switch to your branch and start the FastAPI server:
   ```bash
   git checkout feature/backend-classification
   cd backend
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp ../.env.example .env
   pytest -v
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. Add `ELEVENLABS_API_KEY` (and `GEMINI_API_KEY`) to `backend/.env`.
3. Expose port `8000` over HTTPS so smartphones can scan the QR code and use the camera:
   ```bash
   npx cloudflared tunnel --url http://localhost:8000
   ```
4. Share the generated `https://xxxx.trycloudflare.com` URL with Team A.
5. **Your GitHub Issues:**
   - [Issue #10 — FastAPI Endpoints, Session Store & HTTPS Tunnel](https://github.com/RachmanJasaew/candy-or-curse/issues/10)
   - [Issue #11 — Verified 15-Product DB, Ingredient Classifier & Alternatives](https://github.com/RachmanJasaew/candy-or-curse/issues/11)
   - [Issue #12 — Automated Pytest Suite & ElevenLabs Server Proxy](https://github.com/RachmanJasaew/candy-or-curse/issues/12)

---

## Step 3: Connect Frontend & Backend for the Live Demo

Once Dev B2's tunnel is running:
1. In `frontend/.env` (or Lovable environment settings), set:
   ```env
   VITE_USE_MOCK_API=false
   VITE_API_BASE_URL=https://xxxx.trycloudflare.com
   ```
2. Open the app on the laptop, pick preferences (e.g., **Halal**, **Vegan**, **Peanut Allergy**, or **Eat Everything**), scan the QR code with your phone, and start live-streaming products!
