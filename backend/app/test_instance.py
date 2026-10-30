"""Access-protected wrapper for a temporary phone test. Not a production login system."""
import secrets
from urllib.parse import urlencode
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Mount, Route
from app.main import app as backend

COOKIE = 'candy_test_access'


class TestAccessMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, token: str):
        super().__init__(app)
        self.token = token

    async def dispatch(self, request, call_next):
        supplied = request.query_params.get('access_token', '')
        if supplied and secrets.compare_digest(supplied, self.token):
            query = urlencode([(k, v) for k, v in request.query_params.multi_items() if k != 'access_token'])
            response = RedirectResponse(request.url.path + ('?' + query if query else ''), status_code=303)
            response.set_cookie(COOKIE, self.token, httponly=True, secure=True, samesite='lax')
            response.headers['Cache-Control'] = 'no-store'
            response.headers['Referrer-Policy'] = 'no-referrer'
            return response
        bearer = request.headers.get('authorization', '').removeprefix('Bearer ')
        cookie = request.cookies.get(COOKIE, '')
        if not (secrets.compare_digest(cookie, self.token) or secrets.compare_digest(bearer, self.token)):
            return JSONResponse({'detail': 'Open the private test link provided by the host.'}, status_code=401)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response


def create_test_app(token: str):
    if len(token) < 32:
        raise ValueError('A strong temporary access token is required')
    async def join_link(request):
        return JSONResponse({'join_token': token})
    return Starlette(routes=[Route('/test-access', join_link), Mount('/', app=backend)],
                     middleware=[Middleware(TestAccessMiddleware, token=token)])
