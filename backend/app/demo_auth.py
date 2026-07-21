import base64
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class DemoBasicAuthMiddleware(BaseHTTPMiddleware):
    """Gates every request behind one shared HTTP Basic credential.

    Stands in for real per-user auth on a public demo deployment - not a
    substitute for it. /health is exempt so the host's uptime checks
    don't need the credential.
    """

    def __init__(self, app, username: str, password: str):
        super().__init__(app)
        self.username = username
        self.password = password

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        if self._is_authorized(request.headers.get("authorization")):
            return await call_next(request)

        return Response(
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Claudie demo"'},
        )

    def _is_authorized(self, header: str | None) -> bool:
        if not header or not header.startswith("Basic "):
            return False
        try:
            decoded = base64.b64decode(header[len("Basic "):]).decode()
            user, _, password = decoded.partition(":")
        except Exception:
            return False
        return secrets.compare_digest(user, self.username) and secrets.compare_digest(
            password, self.password
        )
