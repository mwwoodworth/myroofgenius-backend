"""Request authentication middleware enforcing Supabase JWT validation."""

from fastapi import HTTPException
from typing import Iterable, Optional, Sequence
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import logging

from core.supabase_auth import get_current_user

logger = logging.getLogger(__name__)

# Only health checks and explicitly reviewed webhook endpoints are exempt.
DEFAULT_EXEMPT_PATHS: Sequence[str] = (
    "/health",
    "/api/v1/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
    "/api/v1/stripe/webhook",
    "/api/v1/stripe/webhook/test",
    "/api/v1/webhooks/stripe",
    "/api/v1/webhooks/render",
    "/api/v1/revenue/webhook",
    "/webhook/stripe",
)

DEFAULT_EXEMPT_PREFIXES: Sequence[str] = (
    "/docs/",
    "/openapi/",
    "/static/",
    "/public/",
)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces authentication on protected routes."""

    def __init__(
        self,
        app,
        exempt_paths: Optional[Iterable[str]] = None,
        exempt_prefixes: Optional[Iterable[str]] = None,
    ):
        super().__init__(app)
        self.exempt_paths = set(exempt_paths or DEFAULT_EXEMPT_PATHS)
        self.exempt_prefixes = tuple(exempt_prefixes or DEFAULT_EXEMPT_PREFIXES)

    def _is_exempt(self, path: str) -> bool:
        if path in self.exempt_paths:
            return True
        return any(path.startswith(prefix) for prefix in self.exempt_prefixes)

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Allow upstream auth mechanisms (e.g., API key middleware) to satisfy auth.
        if getattr(request.state, "user", None) or getattr(request.state, "authenticated", False):
            return await call_next(request)

        if self._is_exempt(path):
            return await call_next(request)

        authorization = request.headers.get("Authorization") or request.headers.get("authorization")

        try:
            user = await get_current_user(authorization=authorization)
        except HTTPException as exc:
            logger.warning("Authentication failed for %s: %s", path, exc.detail)
            return JSONResponse(
                {"detail": exc.detail},
                status_code=exc.status_code,
                headers=exc.headers or {},
            )

        request.state.user = user
        tenant_id = user.get("tenant_id")
        if tenant_id:
            request.state.tenant_id = tenant_id
        request.state.user_id = user.get("id")

        return await call_next(request)
