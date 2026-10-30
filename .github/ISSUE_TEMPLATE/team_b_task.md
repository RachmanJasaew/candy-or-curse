---
name: Team B Task (Gemma 4 Vision, FastAPI & Ingredient Classifier)
about: Task for Developer B1 (Gemma 4 Vision/Chat) or Developer B2 (FastAPI & Classification)
title: "[Team B] "
labels: ["team-b"]
---

## Developer Owner
- [ ] **Developer B1** (`feature/gemma-vision` — Gemma 4 Vision & Chat)
- [ ] **Developer B2** (`feature/backend-classification` — FastAPI & Ingredient Classification)

## Objective
<!-- Clear description of the endpoint, vision prompt, or classification rule -->

## Owned Files to Modify
- `backend/app/...`

## Acceptance Criteria
- [ ] Adheres strictly to `docs/API_CONTRACT.md` response schemas.
- [ ] Never invents ingredient lists; unknown/unverified products return `YELLOW`.
- [ ] Never describes a product as definitively `"allergy-safe"`.
- [ ] Covered by automated `pytest` tests in `backend/tests/test_api.py`.
