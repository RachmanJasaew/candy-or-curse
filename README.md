# 🎃 Candy or Curse? — Live AI Food & Halloween Candy Scanner

> 👉 **NEW TEAMMATES: Read [START_HERE.md](START_HERE.md) first for your exact branch, commands, and GitHub issues!**

**Candy or Curse?** is an interactive AI food & candy scanner built with **Gemma 4 Vision**, **ElevenLabs Voice (`scribe_v1` & `eleven_flash_v2_5`)**, **Lovable (React + TypeScript)**, and **Python FastAPI**.

### ✨ Key Features
1. **Quick Preference Onboarding & Voice Setup:** Pick **Halal**, **Vegan**, **Vegetarian**, **No Gelatin**, **Eat Everything**, or tell the AI your exact allergies via microphone/chat.
2. **Front-of-Pack OR Ingredient Label OCR / Text Input:** Scan the front of a product, flip it around to scan the back ingredient label, or type/paste ingredients directly.
3. **Live Camera Stream & Conversational Voice Coach:** Stream from your smartphone camera while the AI talks back naturally via ElevenLabs (e.g., *"Okay, I see your bottle. Turn it around—let me see the ingredients!"*).
4. **Smart Alternative Recommendations:** Whenever a product is **Not Recommended (`RED`)**, the app suggests compatible alternatives that match your preferences.

---

## 🚀 Exact Action Plan for All 4 Developers

### Step 1: Clone the Repo
```bash
git clone https://github.com/RachmanJasaew/candy-or-curse.git
cd candy-or-curse
```

### Step 2: Pick Your Role & Branch

| Developer | Branch | Quick Start Commands | GitHub Issues |
| :--- | :--- | :--- | :--- |
| **🎨 Dev A1** *(Lovable & UI)* | `git checkout feature/frontend-ui` | Paste [`docs/LOVABLE_PROMPT.md`](docs/LOVABLE_PROMPT.md) into **Lovable.dev** or edit `frontend/src/pages/*` & `components/*` | [#1](https://github.com/RachmanJasaew/candy-or-curse/issues/1), [#2](https://github.com/RachmanJasaew/candy-or-curse/issues/2), [#3](https://github.com/RachmanJasaew/candy-or-curse/issues/3) |
| **🎙️ Dev A2** *(ElevenLabs Voice & QR)* | `git checkout feature/voice-qr` | `cd frontend && cp ../.env.example .env && npm install && npm run dev` | [#4](https://github.com/RachmanJasaew/candy-or-curse/issues/4), [#5](https://github.com/RachmanJasaew/candy-or-curse/issues/5), [#6](https://github.com/RachmanJasaew/candy-or-curse/issues/6) |
| **👁️ Dev B1** *(Gemma 4 Vision & Coach)* | `git checkout feature/gemma-vision` | Add `GEMINI_API_KEY` to `backend/.env` and test [`backend/app/services/gemma_service.py`](backend/app/services/gemma_service.py) | [#7](https://github.com/RachmanJasaew/candy-or-curse/issues/7), [#8](https://github.com/RachmanJasaew/candy-or-curse/issues/8), [#9](https://github.com/RachmanJasaew/candy-or-curse/issues/9) |
| **⚙️ Dev B2** *(FastAPI, DB & Tunnel)* | `git checkout feature/backend-classification` | `cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && pytest -v && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` | [#10](https://github.com/RachmanJasaew/candy-or-curse/issues/10), [#11](https://github.com/RachmanJasaew/candy-or-curse/issues/11), [#12](https://github.com/RachmanJasaew/candy-or-curse/issues/12) |

### Step 3: Connect Frontend & Backend for the Live Demo
1. **Dev B2** exposes port `8000` over HTTPS so smartphones can connect:
   ```bash
   npx cloudflared tunnel --url http://localhost:8000
   ```
2. **Team A** sets `VITE_USE_MOCK_API=false` and `VITE_API_BASE_URL=https://xxxx.trycloudflare.com` in `frontend/.env`.

---

## 🏗️ Monorepo Structure

```text
candy-or-curse/
├── START_HERE.md                      # Step-by-step developer onboarding plan
├── TEAM_TASKS.md                      # Detailed file ownership & milestones
├── .env.example                       # Environment variable template (Server & Vite)
├── docs/
│   ├── API_CONTRACT.md                # Frozen REST API schemas & safety rules
│   ├── openapi.json                   # OpenAPI 3.1 specification (importable into Lovable)
│   ├── LOVABLE_PROMPT.md              # Copy-paste Lovable prompt & GitHub sync guide
│   └── TEAM_B_IMPLEMENTATION_GUIDE.md # Gemma 4, ElevenLabs, FastAPI & HTTPS tunnel guide
├── frontend/                          # Team A (Dev A1: Lovable UI, Dev A2: Voice & QR Sync)
│   └── src/
│       ├── types/api.ts               # Shared TypeScript interfaces
│       ├── mocks/mockData.ts          # Mock GREEN / RED (+Alternatives) / YELLOW ("Turn it around!")
│       ├── api/client.ts              # Typed API client with VITE_USE_MOCK_API toggle
│       ├── services/voiceRecorder.ts  # ElevenLabs STT/TTS + Web Speech fallback
│       ├── hooks/useSessionSync.ts    # Desktop-to-mobile QR polling hook
│       ├── components/                # ClassificationOverlay (GREEN / RED / YELLOW + Alternatives)
│       └── pages/                     # DesktopHome (/) & MobileScanner (/scan/:sessionId)
└── backend/                           # Team B (Dev B1: Gemma 4 Vision, Dev B2: FastAPI & Classifier)
    ├── app/
    │   ├── main.py                    # FastAPI app & all 6 contract endpoints
    │   ├── data/products.json         # 15 verified products with ingredients & conflict triggers
    │   ├── models/schemas.py          # Pydantic v2 request/response models
    │   └── services/
    │       ├── classifier.py          # Deterministic classifier + OCR/text parser + alternatives
    │       ├── gemma_service.py       # Gemma 4 (`gemma-4-26b-a4b-it`) front + ingredient OCR + coach
    │       ├── session_store.py       # Session & QR sync state store
    │       └── voice_service.py       # ElevenLabs Scribe STT & Flash v2.5 TTS service
    └── tests/
        └── test_api.py                # Automated pytest suite
```
