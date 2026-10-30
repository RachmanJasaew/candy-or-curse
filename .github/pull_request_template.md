## Summary of Changes
<!-- Briefly describe what this PR implements or fixes -->

## Team & Developer Role
- [ ] **Team A — Dev A1** (`feature/frontend-ui`: Lovable & UI)
- [ ] **Team A — Dev A2** (`feature/voice-qr`: Voice & QR Session Integration)
- [ ] **Team B — Dev B1** (`feature/gemma-vision`: Gemma 4 Vision & Conversational AI)
- [ ] **Team B — Dev B2** (`feature/backend-classification`: FastAPI & Ingredient Classification)

## Related GitHub Issue(s)
Closes #

## API Contract & Safety Checklist
- [ ] Matches `docs/API_CONTRACT.md` (or updates both `frontend/src/types/api.ts` and `backend/app/models/schemas.py` if coordinated).
- [ ] No API keys or secrets (`.env`) are committed.
- [ ] Classification logic never claims a product is `"allergy-safe"` or `"100% safe"`.
- [ ] Gemma 4 never invents ingredient lists (`VERIFIED_DATABASE` or `YELLOW` uncertainty only).
- [ ] Tested locally (Frontend compiles / Backend `pytest` passes).
