# CANDY OR CURSE? — Team Coordination, File Ownership & Deliverables

We are **4 developers split into two independent 2-person teams** working in parallel against the frozen API Contract ([`docs/API_CONTRACT.md`](docs/API_CONTRACT.md) and [`docs/openapi.json`](docs/openapi.json)).

---

## 1. Branch & Ownership Matrix (Zero Merge Conflicts)

| Developer | Role | Dedicated Branch | Owned Files / Directories |
| :--- | :--- | :--- | :--- |
| **Dev A1** (Team A) | **Lovable & UI** | `feature/frontend-ui` | `frontend/src/pages/*`, `frontend/src/components/*`, styling, animations, character visuals |
| **Dev A2** (Team A) | **Voice & User Interaction** | `feature/voice-qr` | `frontend/src/api/*`, `frontend/src/services/*`, `frontend/src/hooks/*`, QR session sync, ElevenLabs integration |
| **Dev B1** (Team B) | **Gemma 4 & Computer Vision** | `feature/gemma-vision` | `backend/app/services/gemma_service.py`, vision prompt engineering, confidence calibration, natural-language dietary parser |
| **Dev B2** (Team B) | **Backend & Classification** | `feature/backend-classification` | `backend/app/main.py`, `backend/app/services/classifier.py`, `backend/app/services/session_store.py`, `backend/app/data/products.json`, `backend/tests/*` |

> **Shared Read-Only Contract Files (Modify only via coordinated PR):**
> - [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md) & [`docs/openapi.json`](docs/openapi.json)
> - [`frontend/src/types/api.ts`](frontend/src/types/api.ts) & [`frontend/src/mocks/mockData.ts`](frontend/src/mocks/mockData.ts)
> - [`backend/app/models/schemas.py`](backend/app/models/schemas.py)

---

## 2. TEAM A — FRONTEND & EXPERIENCE (2 Developers)

### Developer A1: Lovable & UI (`feature/frontend-ui`)
**Deliverables:**
- [ ] **Issue A1-1:** Halloween-themed Desktop Landing Page & "The Candy Keeper" AI character stage (`frontend/src/pages/DesktopHome.tsx`).
- [ ] **Issue A1-2:** Responsive Desktop Chat Interface + Active Dietary Restriction pill badges + QR Code Display card.
- [ ] **Issue A1-3:** Mobile Scanning Interface (`/scan/:sessionId` in `frontend/src/pages/MobileScanner.tsx`) with rear smartphone camera preview (`facingMode: "environment"`), snapshot capture, and native camera file input fallback (`<input type="file" accept="image/*" capture="environment" />`).
- [ ] **Issue A1-4:** Dramatic `GREEN` / `RED` / `YELLOW` classification overlays (`frontend/src/components/ClassificationOverlay.tsx`) displaying recognized product, conflicting ingredients, uncertainty reasons, and mandatory safety disclaimer.
- [ ] **Issue A1-5:** Spooky loading states ("Consulting the Cauldron..."), micro-animations, and visual polish.

### Developer A2: Voice & User Interaction (`feature/voice-qr`)
**Deliverables:**
- [ ] **Issue A2-1:** Typed API Client (`frontend/src/api/client.ts`) supporting `VITE_USE_MOCK_API=true` for zero-dependency development and seamless cutover (`VITE_USE_MOCK_API=false`) to Team B's FastAPI URL.
- [ ] **Issue A2-2:** ElevenLabs Speech-to-Text (`POST /api/voice/transcribe`) & Microphone MediaRecorder controller (`frontend/src/services/voiceRecorder.ts`) with error handling and fallback to text input.
- [ ] **Issue A2-3:** ElevenLabs Text-to-Speech (`POST /api/voice/synthesize`) audio playback for "The Candy Keeper" responses and scan verdicts, with browser `window.speechSynthesis` fallback.
- [ ] **Issue A2-4:** QR Session Synchronization (`frontend/src/hooks/useSessionSync.ts`) polling `GET /api/sessions/{id}` on desktop so mobile scans immediately pop up on the big screen during the live demo.

---

## 3. TEAM B — AI & BACKEND (2 Developers)

### Developer B1: Gemma 4 & Computer Vision (`feature/gemma-vision`)
**Deliverables:**
- [ ] **Issue B1-1:** Google AI Studio / Gemini API integration for **Gemma 4** (`gemma-4-26b-a4b-it` / `gemma-4-31b-it`) in `backend/app/services/gemma_service.py`.
- [ ] **Issue B1-2:** Multimodal Candy Wrapper Recognition (`recognize_candy_image`) capable of identifying packaged products (Capri-Sun, Haribo Goldbears, Snickers, M&M's Peanut, Skittles, Reese's, KitKat, Twix, Oreo, Sour Patch Kids, Maoam, Kinder Bueno, Katjes, Trolli, Milky Way) from smartphone photos and returning structured JSON (`RecognizedProduct`, `IdentificationStatus`, confidence, uncertainty reasons).
- [ ] **Issue B1-3:** Strict Anti-Hallucination Guardrails — Gemma 4 must **never** invent ingredient lists and must return `AMBIGUOUS` / `UNKNOWN` when an image is blurry, dark, or unrecognized.
- [ ] **Issue B1-4:** Conversational "Candy Keeper" persona & Natural-Language Dietary Restriction extraction (`chat_with_candy_keeper`).

### Developer B2: Backend & Ingredient Classification (`feature/backend-classification`)
**Deliverables:**
- [ ] **Issue B2-1:** FastAPI application (`backend/app/main.py`) implementing all 6 contract endpoints (`POST /api/sessions`, `GET /api/sessions/{id}`, `POST /api/sessions/{id}/chat`, `POST /api/sessions/{id}/scan`, `POST /api/voice/transcribe`, `POST /api/voice/synthesize`) + CORS & HTTPS tunnel setup.
- [ ] **Issue B2-2:** Verified 15-Product Ingredient & Allergen Database (`backend/app/data/products.json`) with aliases, visual cues, verified ingredients, allergens, cross-contact warnings, and dietary flags.
- [ ] **Issue B2-3:** Deterministic `GREEN` / `RED` / `YELLOW` Classification Engine (`backend/app/services/classifier.py`) that checks allergies, vegan/vegetarian rules, gelatin/pork avoidance, halal/kosher preferences, and **never claims a product is definitively allergy-safe**.
- [ ] **Issue B2-4:** Automated `pytest` test suite (`backend/tests/test_api.py`) covering all endpoints and safety invariants.

---

## 4. Milestones & Integration Checkpoints

### Milestone 1: Foundation & API Contract (Hour 0 – Hour 1) — *COMPLETED*
- [x] Shared API Contract (`docs/API_CONTRACT.md` & `docs/openapi.json`) defined.
- [x] Backend skeleton, 15-product verified database, and mock-capable frontend client created.
- [x] All 4 developer feature branches created from `main`.

### Milestone 2: Core Recognition & Classification MVP (Hour 1 – Hour 4)
- [ ] **Parallel Track A:** Dev A1 generates/polishes UI in Lovable using `docs/LOVABLE_PROMPT.md`; Dev A2 wires QR session sync and mock API calls.
- [ ] **Parallel Track B:** Dev B1 tests real candy wrapper photos against `gemma-4-26b-a4b-it`; Dev B2 exposes FastAPI over HTTPS (via `cloudflared tunnel` or `ngrok`) and verifies all `pytest` tests pass.
- [ ] **Integration Checkpoint 1 (End of Hour 4):** Flip `VITE_USE_MOCK_API=false`, point `VITE_API_BASE_URL` to Team B's tunnel URL, and complete the **First Working End-to-End Test** (create session -> scan QR on phone -> snap photo of Haribo/Snickers/Capri-Sun -> see real `RED`/`GREEN`/`YELLOW` verdict).

### Milestone 3: Voice, QR Sync & Live Demo Polish (Hour 4 – Hour 7)
- [ ] Connect live ElevenLabs `scribe_v1` STT and `eleven_flash_v2_5` TTS (`ELEVENLABS_API_KEY`).
- [ ] Verify desktop screen updates automatically within 2.5 seconds when mobile phone scans a candy.
- [ ] Rehearse the 3-candy stage demo:
  1. **Capri-Sun Multivitamin** (Vegan + Peanut allergy user) $\rightarrow$ **GREEN**
  2. **Haribo Goldbears** or **Snickers** (Vegan + Peanut allergy user) $\rightarrow$ **RED**
  3. **Unlabeled / Mystery Candy** $\rightarrow$ **YELLOW**

---

## 5. Git Workflow Rules (Minimize Merge Conflicts)

1. Work on your assigned branch (`feature/frontend-ui`, `feature/voice-qr`, `feature/gemma-vision`, `feature/backend-classification`).
2. Pull latest `main` before opening a PR:
   ```bash
   git fetch origin
   git rebase origin/main
   ```
3. Open a Pull Request into `main` at each Integration Checkpoint. CI (`.github/workflows/ci.yml`) will automatically verify Python compilation, `pytest`, and TypeScript types.
