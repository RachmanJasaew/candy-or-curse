from fastapi.testclient import TestClient
from app.test_instance import create_test_app
from app.config import settings
from app.services import voice_service
import httpx
import pytest

TOKEN = 'test-token-with-at-least-32-characters-long'


def test_tunnel_requires_access_for_every_endpoint():
    c = TestClient(create_test_app(TOKEN), base_url='https://phone.test')
    for path in ['/', '/api/health', '/api/products', '/docs', '/test-access', '/scan/unknown']:
        assert c.get(path).status_code == 401
    r = c.get('/?access_token=' + TOKEN)
    assert r.status_code == 200
    assert 'access_token' not in str(r.url)
    assert c.get('/api/health').status_code == 200
    assert c.get('/test-access').json()['join_token'] == TOKEN
    assert c.get('/').headers['referrer-policy'] == 'no-referrer'
    other_phone = TestClient(create_test_app(TOKEN), base_url='https://phone.test')
    assert other_phone.get('/api/health').status_code == 401
    assert other_phone.get('/api/health', headers={'Authorization':'Bearer ' + TOKEN}).status_code == 200


def test_weak_test_access_token_is_rejected():
    with pytest.raises(ValueError): create_test_app('short')


def test_failed_voice_transcription_returns_error_not_fake_preferences(monkeypatch):
    from app.main import app
    monkeypatch.setattr(settings, 'ELEVENLABS_API_KEY', 'test-key')
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, **kwargs):
            return httpx.Response(401, request=httpx.Request('POST',url), json={})
    monkeypatch.setattr(voice_service.httpx, 'AsyncClient', Client)
    r = TestClient(app).post('/api/voice/transcribe', files={'audio': ('test.mp4',b'audio','audio/mp4')})
    assert r.status_code == 502
    assert 'text' not in r.json()
