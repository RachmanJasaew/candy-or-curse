# 🎃 Candy or Curse? — AI Halloween Candy Scanner

**Candy or Curse?** is a Halloween-themed AI candy scanner built with **Gemma 4 Vision**, **ElevenLabs Voice (`scribe_v1` & `eleven_flash_v2_5`)**, **Lovable (React + TypeScript)**, and **Python FastAPI**.

Users tell **The Candy Keeper** their dietary restrictions (allergies, vegan requirements, gelatin avoidance, halal/kosher preferences) by voice or text on desktop, scan a session QR code with their smartphone, and snap a photo of any Halloween candy wrapper to receive an instant **GREEN / RED / YELLOW** verdict backed by a verified ingredient database.

---

## 🏗️ Monorepo Structure

```text
candy-or-curse/
├── .env.example                       # Environment variable template (Server & Vite)
├── TEAM_TASKS.md                      # 4-Developer split (Team A & Team B), branches, and milestones
├── docs/
│   ├── API_CONTRACT.md                # Frozen REST API schemas & safety rules
│   ├── openapi.json                   # OpenAPI 3.1 specification (importable into Lovable)
│   ├── LOVABLE_PROMPT.md              # Copy-paste Lovable prompt & GitHub two-way sync guide
│   └── TEAM_B_IMPLEMENTATION_GUIDE.md # Gemma 4, ElevenLabs, FastAPI & HTTPS tunnel guide
├── frontend/                          # Team A (Dev A1: Lovable UI, Dev A2: Voice & QR Sync)
│   ├── package.json
│   └── src/
│       ├── types/api.ts               # Shared TypeScript interfaces matching API_CONTRACT.md
│       ├── mocks/mockData.ts          # Mock GREEN / RED / YELLOW responses for offline UI dev
│       ├── api/client.ts              # Typed API client with VITE_USE_MOCK_API toggle
│       ├── services/voiceRecorder.ts  # ElevenLabs STT/TTS + Web Speech fallback
│       ├── hooks/useSessionSync.ts    # Desktop-to-mobile QR polling hook
│       ├── components/                # ClassificationOverlay (GREEN / RED / YELLOW)
│       └── pages/                     # DesktopHome (/) & MobileScanner (/scan/:sessionId)
├── backend/                           # Team B (Dev B1: Gemma 4 Vision, Dev B2: FastAPI & Classifier)
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                    # FastAPI app & all 6 contract endpoints
│   │   ├── config.py                  # Env settings (GEMINI_API_KEY, ELEVENLABS_API_KEY)
│   │   ├── data/products.json         # 15 verified candies with ingredients & conflict triggers
│   │   ├── models/schemas.py          # Pydantic v2 request/response models
│   │   └── services/
│   │       ├── classifier.py          # Deterministic GREEN / RED / YELLOW classifier
│   │       ├── gemma_service.py       # Gemma 4 (`gemma-4-26b-a4b-it`) vision & chat service
│   │       ├── session_store.py       # Session & QR sync state store
│   │       └── voice_service.py       # ElevenLabs Scribe STT & Flash v2.5 TTS service
│   └── tests/
│       └── test_api.py                # Automated pytest suite
└── scripts/
    ├── setup_github.sh                # Creates private repo, pushes 5 branches, milestones & 12 issues
    └── sync_lovable.sh                # Syncs a Lovable GitHub repo into frontend/
```

---

## 🚀 Quick Start

### 1. Backend (Team B — FastAPI + Gemma 4 + ElevenLabs)
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
# Add GEMINI_API_KEY and ELEVENLABS_API_KEY to backend/.env (works in mock mode even without keys!)

pytest -v
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend (Team A — Lovable / React + Vite)
```bash
cd frontend
cp ../.env.example .env
# Keep VITE_USE_MOCK_API=true while developing UI independently, or set VITE_USE_MOCK_API=false to hit FastAPI
npm install
npm run dev
```

---

## 🛡️ Safety & Classification Policy
- **GREEN:** Recognized product matches our verified 15-product database (`VERIFIED_DATABASE`) and has **no known conflicting ingredients** for the user's active restrictions.
- **RED:** Recognized product contains at least one **verified conflicting ingredient** or allergen cross-contact warning.
- **YELLOW:** Product is unrecognized, visual confidence is `< 60%`, or product is not in our verified database (`NONE`).
- **Strict Medical Disclaimer:** The system **never** describes any product as *"allergy-safe"* or *"100% safe"*, and Gemma 4 is strictly forbidden from inventing ingredient lists.
