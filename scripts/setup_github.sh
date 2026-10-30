#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# CANDY OR CURSE? — Automated GitHub Repository, Branch, Milestone & Issue Setup
# Run this script once authenticated with GitHub CLI (`gh auth login`).
# ==============================================================================

REPO_NAME="${1:-candy-or-curse}"

echo "🎃 Checking GitHub CLI authentication..."
if ! gh auth status >/dev/null 2>&1; then
  echo "⚠️  GitHub CLI is not authenticated yet."
  echo "👉 Please run: gh auth login"
  echo "   Then re-run: ./scripts/setup_github.sh"
  exit 1
fi

GH_USER="$(gh api user -q .login)"
FULL_REPO="${GH_USER}/${REPO_NAME}"
echo "✅ Authenticated as GitHub user: ${GH_USER}"

# 1. Check if repository already exists (e.g. from Lovable or previous run)
if gh repo view "${FULL_REPO}" >/dev/null 2>&1; then
  echo "ℹ️  Repository ${FULL_REPO} already exists. Linking remote 'origin'..."
  RepoURL="https://github.com/${FULL_REPO}.git"
  if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "${RepoURL}"
  else
    git remote add origin "${RepoURL}"
  fi
else
  echo "🚀 Creating PRIVATE GitHub repository: ${FULL_REPO}..."
  gh repo create "${REPO_NAME}" \
    --private \
    --source=. \
    --remote=origin \
    --description "Candy or Curse? — Halloween AI Candy Scanner (Gemma 4 + ElevenLabs + Lovable + FastAPI)"
fi

# 2. Push main and all 4 developer feature branches
echo "🌿 Pushing main and all 4 developer branches to origin..."
git push -u origin main
for branch in feature/frontend-ui feature/voice-qr feature/gemma-vision feature/backend-classification; do
  git push -u origin "${branch}"
done

# 3. Create Team & Developer Labels
echo "🏷️  Creating GitHub labels..."
gh label create "team-a" --color "f97316" --description "Team A: Frontend & Experience" --force
gh label create "team-b" --color "8b5cf6" --description "Team B: AI & Backend" --force
gh label create "dev-a1" --color "fb923c" --description "Developer A1: Lovable & UI" --force
gh label create "dev-a2" --color "fdba74" --description "Developer A2: Voice & User Interaction" --force
gh label create "dev-b1" --color "a78bfa" --description "Developer B1: Gemma 4 & Computer Vision" --force
gh label create "dev-b2" --color "c4b5fd" --description "Developer B2: FastAPI & Ingredient Classification" --force
gh label create "mvp" --color "10b981" --description "Critical path for first E2E demo" --force

# 4. Create Milestones
echo "🏁 Creating Milestones..."
M1_TITLE="M1: API Contract & Skeleton"
M2_TITLE="M2: Core Recognition & Classification MVP"
M3_TITLE="M3: Voice, QR Sync & Live Demo Polish"

gh api "repos/${FULL_REPO}/milestones" -f title="${M1_TITLE}" -f description="Shared API contracts, repo structure, mock data, and branches." >/dev/null 2>&1 || true
gh api "repos/${FULL_REPO}/milestones" -f title="${M2_TITLE}" -f description="First end-to-end working scan: Dietary input -> QR code -> Mobile camera photo -> Gemma 4 + Verified DB -> GREEN/RED/YELLOW." >/dev/null 2>&1 || true
gh api "repos/${FULL_REPO}/milestones" -f title="${M3_TITLE}" -f description="ElevenLabs STT/TTS voice interaction, desktop polling sync, and Halloween visual polish." >/dev/null 2>&1 || true

# 5. Create 12 Actionable GitHub Issues (Grouped by Team A and Team B)
echo "📋 Creating GitHub Issues for Team A and Team B..."

# --- Developer A1 Issues ---
gh issue create \
  --title "[Team A | Dev A1] Halloween Landing Page & 'The Candy Keeper' Desktop Chat UI" \
  --label "team-a,dev-a1,mvp" \
  --milestone "${M2_TITLE}" \
  --body "### Owner: Developer A1 (\`feature/frontend-ui\`)
**Files:** \`frontend/src/pages/DesktopHome.tsx\`, \`docs/LOVABLE_PROMPT.md\`

#### Tasks:
- [ ] Build Halloween-themed desktop interface featuring 'The Candy Keeper' character.
- [ ] Display active dietary restriction pill badges (\`peanuts\`, \`vegan\`, \`no_gelatin\`, etc.).
- [ ] Display session QR code card linking to \`/scan/:sessionId\`.
- [ ] Render live latest scan result synced from mobile."

gh issue create \
  --title "[Team A | Dev A1] Mobile Camera Scanner View (/scan/:sessionId)" \
  --label "team-a,dev-a1,mvp" \
  --milestone "${M2_TITLE}" \
  --body "### Owner: Developer A1 (\`feature/frontend-ui\`)
**Files:** \`frontend/src/pages/MobileScanner.tsx\`

#### Tasks:
- [ ] Implement mobile-first route \`/scan/:sessionId\` showing active session dietary badges.
- [ ] Support rear smartphone camera preview (\`facingMode: environment\`) and photo snapshot capture.
- [ ] Include native file/camera input fallback (\`accept=\"image/*\" capture=\"environment\"\`) for iOS Safari reliability."

gh issue create \
  --title "[Team A | Dev A1] GREEN / RED / YELLOW Classification Overlays & Spooky Animations" \
  --label "team-a,dev-a1,mvp" \
  --milestone "${M3_TITLE}" \
  --body "### Owner: Developer A1 (\`feature/frontend-ui\`)
**Files:** \`frontend/src/components/ClassificationOverlay.tsx\`

#### Tasks:
- [ ] Build distinct full-card visual overlays for \`GREEN\` (No known conflicts), \`RED\` (Verified conflict), and \`YELLOW\` (Uncertain/Unverified).
- [ ] Highlight \`conflicting_ingredients\` on RED and \`uncertainty.reasons\` on YELLOW.
- [ ] Always render \`safety_disclaimer\` (never claim a product is 100% allergy-safe)."

# --- Developer A2 Issues ---
gh issue create \
  --title "[Team A | Dev A2] Frontend API Client, Mock Toggle & QR Session Polling" \
  --label "team-a,dev-a2,mvp" \
  --milestone "${M2_TITLE}" \
  --body "### Owner: Developer A2 (\`feature/voice-qr\`)
**Files:** \`frontend/src/api/client.ts\`, \`frontend/src/hooks/useSessionSync.ts\`

#### Tasks:
- [ ] Wire typed API client with \`VITE_USE_MOCK_API\` flag so Team A works offline and switches cleanly to Team B's FastAPI URL.
- [ ] Poll \`GET /api/sessions/{id}\` every 2.5s on desktop so mobile scans update the desktop view automatically.
- [ ] Ensure QR code uses an HTTPS public URL (\`VITE_PUBLIC_APP_URL\`)."

gh issue create \
  --title "[Team A | Dev A2] ElevenLabs Speech-to-Text Microphone Integration" \
  --label "team-a,dev-a2" \
  --milestone "${M3_TITLE}" \
  --body "### Owner: Developer A2 (\`feature/voice-qr\`)
**Files:** \`frontend/src/services/voiceRecorder.ts\`, \`frontend/src/pages/DesktopHome.tsx\`

#### Tasks:
- [ ] Capture microphone audio via \`MediaRecorder\` and upload to \`POST /api/voice/transcribe\`.
- [ ] Send transcribed text to \`POST /api/sessions/{id}/chat\` to update dietary restrictions.
- [ ] Gracefully fall back to text chat if mic permission is denied or API fails."

gh issue create \
  --title "[Team A | Dev A2] ElevenLabs Text-to-Speech Playback for The Candy Keeper" \
  --label "team-a,dev-a2" \
  --milestone "${M3_TITLE}" \
  --body "### Owner: Developer A2 (\`feature/voice-qr\`)
**Files:** \`frontend/src/services/voiceRecorder.ts\`

#### Tasks:
- [ ] Play base64 MP3 audio returned by \`POST /api/voice/synthesize\` when The Candy Keeper replies or announces a scan verdict.
- [ ] Fall back to browser \`window.speechSynthesis\` if offline."

# --- Developer B1 Issues ---
gh issue create \
  --title "[Team B | Dev B1] Gemma 4 Multimodal Vision Candy Wrapper Recognition" \
  --label "team-b,dev-b1,mvp" \
  --milestone "${M2_TITLE}" \
  --body "### Owner: Developer B1 (\`feature/gemma-vision\`)
**Files:** \`backend/app/services/gemma_service.py\`

#### Tasks:
- [ ] Integrate Google AI Studio API with \`gemma-4-26b-a4b-it\` (or \`gemma-4-31b-it\`).
- [ ] Recognize packaged products (Capri-Sun, Haribo Goldbears, Snickers, M&M's Peanut, Skittles, Reese's, KitKat, Twix, Oreo, etc.) from mobile camera snapshots.
- [ ] Return structured JSON with \`product_id\`, \`name\`, \`confidence\`, \`identification_status\`, and \`visual_evidence\`."

gh issue create \
  --title "[Team B | Dev B1] Anti-Hallucination & Ambiguous/Unknown Image Guardrails" \
  --label "team-b,dev-b1,mvp" \
  --milestone "${M2_TITLE}" \
  --body "### Owner: Developer B1 (\`feature/gemma-vision\`)
**Files:** \`backend/app/services/gemma_service.py\`

#### Tasks:
- [ ] Enforce strict system prompt rule: Gemma 4 must NEVER invent or guess ingredient lists.
- [ ] Return \`AMBIGUOUS\` or \`UNKNOWN\` when wrapper is blurry, dark, or unrecognized so the backend classifies it as \`YELLOW\`."

gh issue create \
  --title "[Team B | Dev B1] Conversational Candy Keeper Chat & Dietary Restriction Extraction" \
  --label "team-b,dev-b1" \
  --milestone "${M3_TITLE}" \
  --body "### Owner: Developer B1 (\`feature/gemma-vision\`)
**Files:** \`backend/app/services/gemma_service.py\`

#### Tasks:
- [ ] Implement \`chat_with_candy_keeper\` to respond in spooky character and extract normalized restriction tags from natural-language user input."

# --- Developer B2 Issues ---
gh issue create \
  --title "[Team B | Dev B2] FastAPI Endpoints, Session Store & HTTPS Tunnel Setup" \
  --label "team-b,dev-b2,mvp" \
  --milestone "${M2_TITLE}" \
  --body "### Owner: Developer B2 (\`feature/backend-classification\`)
**Files:** \`backend/app/main.py\`, \`backend/app/services/session_store.py\`

#### Tasks:
- [ ] Implement and verify \`POST /api/sessions\`, \`GET /api/sessions/{id}\`, \`POST /api/sessions/{id}/chat\`, \`POST /api/sessions/{id}/scan\`, \`POST /api/voice/transcribe\`, and \`POST /api/voice/synthesize\`.
- [ ] Expose backend via HTTPS tunnel (\`cloudflared\` or \`ngrok\`) for mobile scanning."

gh issue create \
  --title "[Team B | Dev B2] Verified 15-Product Ingredient Database & Deterministic Classifier" \
  --label "team-b,dev-b2,mvp" \
  --milestone "${M2_TITLE}" \
  --body "### Owner: Developer B2 (\`feature/backend-classification\`)
**Files:** \`backend/app/data/products.json\`, \`backend/app/services/classifier.py\`

#### Tasks:
- [ ] Maintain verified ingredient lists, allergens, and dietary flags for 15 popular Halloween treats.
- [ ] Implement deterministic \`GREEN\` / \`RED\` / \`YELLOW\` classification logic.
- [ ] Ensure responses NEVER describe any product as 'allergy-safe' or '100% safe'."

gh issue create \
  --title "[Team B | Dev B2] Automated Backend Pytest Suite & ElevenLabs Server Proxy" \
  --label "team-b,dev-b2,mvp" \
  --milestone "${M3_TITLE}" \
  --body "### Owner: Developer B2 (\`feature/backend-classification\`)
**Files:** \`backend/tests/test_api.py\`, \`backend/app/services/voice_service.py\`

#### Tasks:
- [ ] Maintain automated \`pytest\` coverage for \`GREEN\`, \`RED\`, and \`YELLOW\` scan flows, chat updates, and voice endpoints.
- [ ] Proxy ElevenLabs \`scribe_v1\` STT and \`eleven_flash_v2_5\` TTS keeping API keys strictly server-side."

echo ""
echo "🎉 GitHub Repository Setup Complete!"
echo "🔗 Repository URL: https://github.com/${FULL_REPO}"
echo "🔗 Issues List:    https://github.com/${FULL_REPO}/issues"
