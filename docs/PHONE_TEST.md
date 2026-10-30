# Temporary phone test

The backend-served frontend (`frontend/dist/index.html`) is the interface for this test.
It includes camera/upload scanning, typed chat, microphone transcription with a review
step before Send, browser speech fallback, and a QR code for the same session.

## Access protection

Use `create_test_app(token)` from `app.test_instance` when exposing a test server.
It wraps every route, including docs and session APIs, with temporary token access.
Use a random token of at least 32 characters. The entry link's `access_token` query
parameter establishes a Secure, HttpOnly, SameSite=Lax session cookie and is removed
from the URL. Authenticated pages obtain a join token for the phone QR link.
Unauthenticated requests return 401. Disable access logs so entry-link tokens are not
logged. Private links should only be shared with intended testers. This wrapper is
for a temporary test and is not a production account/authentication system.

The running instance and its access token are local runtime state, not repository
configuration. The temporary tunnel requires the host computer and processes to stay
running. Tunnel URLs can expire/change. Do not commit live URLs with access tokens,
API keys, or captured audio/images.

## Voice behavior

Set a valid `ELEVENLABS_API_KEY` in backend/.env, then restart the backend to reload it.
Missing transcription credentials return 503; provider failure returns 502; empty
speech returns 422. No failed transcription is replaced with dietary preferences.
Microphone text is placed in the chat box for review and never sent as chat until
the user presses Send. MP4 recording is supported when the browser chooses it.
Text input and browser speech output remain available if ElevenLabs is unavailable.

## Checks before sharing

From backend, run `GEMINI_API_KEY='' ELEVENLABS_API_KEY='' .venv/bin/python -m pytest -q`.
From frontend, run `node --test tests/served-ui.test.cjs`.
The served UI tests run before the Vite build in CI because the standalone served
page and React build are currently separate artifacts.

Current checks: 30 backend tests and 3 served-UI behavior tests pass. HTTPS smoke
verified 401 without access and 200 for the authenticated app and health endpoint.
The browser rendered the desktop interface and matching-session QR code.

## Real-device sequence

1. Open the private entry link on the laptop and choose actual dietary preferences.
2. Scan the page's QR code with the phone, granting camera permission when prompted.
3. Photograph the front of a product; if requested, photograph one full ingredient block.
4. Verify the phone and laptop show the same session ID and latest scan result.
5. Check typed ingredient input and unreadable-photo uncertainty behavior.
6. With a working voice key, record a short phrase, stop, review the transcript, and Send.
7. Confirm errors do not change the profile and repeat a capture without restarting the camera.

At setup, ElevenLabs rejected the supplied key with 401 invalid_api_key; formatting
checks were clean. Voice provider validation remains blocked until the key owner
confirms or replaces it. This does not block typed chat and camera testing.
