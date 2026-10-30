"""Check live Gemma without sending photos or personal data.

Run: backend/.venv/bin/python scripts/check_gemma.py
Exit 0 means live generation succeeded; exit 1 means it did not.
"""
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
import httpx
from app.config import settings


async def main():
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.startswith('your_'):
        print('Set GEMINI_API_KEY in backend/.env first.')
        return 1
    if settings.GEMINI_API_KEY.startswith('AQ.'):
        from app.services.gemma_service import _generate, _response_text
        try:
            data = await _generate({'contents': [{'parts': [{'text': 'Say hello.'}]}]})
            print('Vertex live text received:', bool(_response_text(data)))
            return 0
        except Exception as exc:
            print('Vertex check failed:', type(exc).__name__)
            return 1
    headers = {'x-goog-api-key': settings.GEMINI_API_KEY}
    base = 'https://generativelanguage.googleapis.com/v1beta'
    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
        try:
            response = await client.get(f'{base}/models', headers=headers)
            print('Model listing HTTP:', response.status_code)
            if not response.is_success:
                return 1
            available = {m['name'] for m in response.json().get('models', [])}
            if f'models/{settings.GEMMA_MODEL}' not in available:
                print('Configured model is not available:', settings.GEMMA_MODEL)
                return 1
            response = await client.post(
                f'{base}/models/{settings.GEMMA_MODEL}:generateContent',
                headers=headers,
                json={'contents': [{'parts': [{'text': 'Say hello.'}]}],
                      'generationConfig': {'thinkingConfig': {'thinkingLevel': 'minimal'}}},
            )
            print('Live generation HTTP:', response.status_code)
            if not response.is_success:
                print('Provider status:', response.json().get('error', {}).get('status', 'unknown'))
                return 1
            candidates = response.json().get('candidates', [])
            has_text = any(
                isinstance(p.get('text'), str) and p['text'].strip()
                for candidate in candidates
                for p in candidate.get('content', {}).get('parts', [])
                if not p.get('thought')
            )
            print('Live text received:', has_text)
            return 0 if has_text else 1
        except (httpx.HTTPError, ValueError) as exc:
            # Exception strings may contain credential-bearing request information.
            print('Connection check failed:', type(exc).__name__)
            return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
