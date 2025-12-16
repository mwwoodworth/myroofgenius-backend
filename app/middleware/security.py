"""
Security middleware for rate limiting, API key validation, and request protection
"""

import time
import hashlib
import hmac
from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable, Iterable, Sequence
from datetime import datetime, timedelta
import redis
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import json

try:
    from app.core.config import settings  # type: ignore
    _settings_import_error: Optional[Exception] = None
except Exception as exc:  # pragma: no cover - fallback for misconfigured environments
    settings = None  # type: ignore[assignment]
    _settings_import_error = exc

from app.core.exceptions import RateLimitError

logger = logging.getLogger(__name__)

if settings is None:  # pragma: no cover - exercised when config import fails
    logger.warning(
        "Falling back to default security settings because app.core.config failed to load: %s",
        _settings_import_error,
    )

    class _FallbackSettings:
        RATE_LIMIT_REQUESTS = 100
        RATE_LIMIT_PERIOD = 60
        is_production = False
        redis_url = None

    settings = _FallbackSettings()  # type: ignore[assignment]


@dataclass
class _CachedAPIKey:
    """Cached API key metadata to avoid repeated database lookups."""

    key_id: str
    expires_at_ts: Optional[float]
    cache_expiry_ts: float
    last_touch_ts: float


# Keep aligned with middleware.authentication.DEFAULT_EXEMPT_PATHS.
DEFAULT_PUBLIC_PATHS: Sequence[str] = (
    "/health",
    "/api/v1/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/erp/public",
    "/api/v1/stripe/webhook",
    "/api/v1/stripe/webhook/test",
    "/api/v1/webhooks/stripe",
    "/api/v1/webhooks/render",
    "/api/v1/revenue/webhook",
    "/webhook/stripe",
    "/api/v1/logs/vercel",  # Vercel log drain - no auth needed
    "/api/v1/logs/render",  # Render log drain - no auth needed
)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    DEPRECATED: This middleware is unused. The application uses middleware/rate_limiter.py instead.
    Keeping for reference only - do NOT enable without ensuring it matches the active implementation.

    Rate limiting middleware using Redis
    Implements sliding window algorithm
    """
    
    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self.redis_client = redis_client
        self.rate_limit = settings.RATE_LIMIT_REQUESTS
        self.window_seconds = settings.RATE_LIMIT_PERIOD
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/", "/health", "/api/v1/health"]:
            return await call_next(request)
        
        # Skip if Redis not available
        if not self.redis_client:
            return await call_next(request)
        
        # Get client identifier (IP or API key)
        client_id = self._get_client_id(request)
        
        try:
            # Check rate limit
            if not await self._check_rate_limit(client_id):
                raise RateLimitError(
                    "Rate limit exceeded",
                    retry_after=self.window_seconds
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
            response.headers["X-RateLimit-Window"] = str(self.window_seconds)
            
            return response
            
        except RateLimitError:
            raise
        except Exception as e:
            logger.error(f"Rate limit middleware error: {str(e)}")
            return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request"""
        # Check for API key first
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return f"api_key:{hashlib.md5(auth_header.encode()).hexdigest()}"
        
        # Use IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        try:
            key = f"rate_limit:{client_id}"
            current_time = int(time.time())
            window_start = current_time - self.window_seconds
            
            # Remove old entries
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count requests in window
            request_count = self.redis_client.zcard(key)
            
            if request_count >= self.rate_limit:
                return False
            
            # Add current request
            self.redis_client.zadd(key, {str(current_time): current_time})
            self.redis_client.expire(key, self.window_seconds)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis error in rate limiting: {str(e)}")
            return True  # Allow request if Redis fails

class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    API key validation middleware with in-memory caching to minimize database lookups.
    """

    def __init__(
        self,
        app,
        *,
        cache_ttl_seconds: int = 300,
        usage_touch_interval_seconds: int = 30,
        max_cache_entries: int = 512,
        public_paths: Optional[Iterable[str]] = None,
    ):
        super().__init__(app)
        self.public_paths: Sequence[str] = (
            tuple(public_paths) if public_paths is not None else DEFAULT_PUBLIC_PATHS
        )
        self.cache_ttl = max(cache_ttl_seconds, 1)
        self.usage_touch_interval = max(usage_touch_interval_seconds, 1)
        self.max_cache_entries = max_cache_entries if max_cache_entries > 0 else 512
        self._cache: "OrderedDict[str, _CachedAPIKey]" = OrderedDict()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip validation for public paths
        if any(request.url.path.startswith(path) for path in self.public_paths):
            logger.debug("Skipping API key validation for public path %s", request.url.path)
            return await call_next(request)

        # Check for API key
        api_key = self._extract_api_key(request)

        if api_key:
            db_pool = getattr(request.app.state, "db_pool", None)

            cache_entry = await self._validate_api_key(api_key, db_pool)
            if cache_entry:
                # Attach context to the request for downstream processing
                request.state.api_key = api_key
                request.state.api_key_id = cache_entry.key_id
                request.state.authenticated = True
                request.state.user = {
                    "id": f"api_key:{cache_entry.key_id}",
                    "role": "service",
                    "tenant_id": None,
                    "auth_type": "api_key",
                }
                request.state.user_id = cache_entry.key_id
            else:
                # Return JSONResponse directly - HTTPException from middleware may not
                # reach app exception handlers, causing 500 instead of 401
                from starlette.responses import JSONResponse
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid API key"},
                    headers={"WWW-Authenticate": "ApiKey"},
                )

        return await call_next(request)

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request headers."""
        auth_header = request.headers.get("Authorization") or request.headers.get("authorization") or ""
        if auth_header.startswith("ApiKey "):
            return auth_header[len("ApiKey ") :].strip()

        if auth_header.startswith("Bearer "):
            # Bearer tokens should always be handled by AuthenticationMiddleware,
            # not treated as API keys. This prevents non-JWT Bearer tokens from
            # being incorrectly validated as API keys (causing 500 errors).
            return None

        return request.headers.get("X-API-Key") or request.headers.get("x-api-key")

    async def _validate_api_key(self, api_key: str, db_pool) -> Optional[_CachedAPIKey]:
        """Validate API key against database with caching."""
        if not api_key or len(api_key) < 16:
            return None

        if not db_pool:
            logger.error("Database pool unavailable for API key validation")
            return None

        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        now = time.time()

        cache_entry = self._cache.get(key_hash)
        if cache_entry:
            if cache_entry.expires_at_ts and cache_entry.expires_at_ts <= now:
                logger.info("Cached API key has expired; removing from cache")
                self._cache.pop(key_hash, None)
            elif cache_entry.cache_expiry_ts <= now:
                logger.debug("API key cache entry exceeded TTL; refreshing from database")
                self._cache.pop(key_hash, None)
            else:
                if now - cache_entry.last_touch_ts < self.usage_touch_interval:
                    # Entry still fresh; extend TTL and return
                    cache_entry.cache_expiry_ts = now + self.cache_ttl
                    self._cache.move_to_end(key_hash)
                    return cache_entry

                # Refresh usage metadata in the database
                if await self._touch_cached_entry(cache_entry, db_pool, now):
                    self._cache.move_to_end(key_hash)
                    return cache_entry

                # Touch failed (key revoked/expired)
                self._cache.pop(key_hash, None)

        # Cache miss or expired entry; fetch from database
        refreshed_entry = await self._fetch_and_cache_key(key_hash, db_pool, now)
        if refreshed_entry:
            self._cache[key_hash] = refreshed_entry
            self._cache.move_to_end(key_hash)
            self._prune_cache()
            return refreshed_entry

        return None

    async def _touch_cached_entry(
        self,
        cache_entry: _CachedAPIKey,
        db_pool,
        now: float,
    ) -> bool:
        """Update usage telemetry for a cached API key and ensure it is still valid."""
        try:
            async with db_pool.acquire() as conn:
                record = await conn.fetchrow(
                    """
                    UPDATE api_keys
                    SET last_used_at = NOW(),
                        usage_count = COALESCE(usage_count, 0) + 1
                    WHERE id = $1
                      AND (is_active IS NULL OR is_active = TRUE)
                      AND (expires_at IS NULL OR expires_at > NOW())
                    RETURNING expires_at
                    """,
                    cache_entry.key_id,
                )
        except Exception as error:
            logger.error("API key usage update error: %s", error)
            return False

        if not record:
            return False

        cache_entry.last_touch_ts = now
        cache_entry.cache_expiry_ts = now + self.cache_ttl
        expires_at = record.get("expires_at")
        cache_entry.expires_at_ts = (
            expires_at.timestamp() if isinstance(expires_at, datetime) else None
        )
        return True

    async def _fetch_and_cache_key(
        self,
        key_hash: str,
        db_pool,
        now: float,
    ) -> Optional[_CachedAPIKey]:
        """Fetch API key information from the database and return a cache entry."""
        try:
            async with db_pool.acquire() as conn:
                record = await conn.fetchrow(
                    """
                    UPDATE api_keys
                    SET last_used_at = NOW(),
                        usage_count = COALESCE(usage_count, 0) + 1
                    WHERE key_hash = $1
                      AND (is_active IS NULL OR is_active = TRUE)
                      AND (expires_at IS NULL OR expires_at > NOW())
                    RETURNING id, expires_at
                    """,
                    key_hash,
                )
        except Exception as error:
            logger.error("API key validation error: %s", error)
            return None

        if not record:
            return None

        expires_at = record.get("expires_at")
        expires_at_ts = (
            expires_at.timestamp() if isinstance(expires_at, datetime) else None
        )

        return _CachedAPIKey(
            key_id=str(record["id"]),
            expires_at_ts=expires_at_ts,
            cache_expiry_ts=now + self.cache_ttl,
            last_touch_ts=now,
        )

    def _prune_cache(self) -> None:
        """Ensure the cache does not exceed the configured size."""
        while len(self._cache) > self.max_cache_entries:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Evicted API key hash from cache: %s", evicted_key)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        
        # Add CSP for production
        if settings.is_production:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https://api.stripe.com"
            )
        
        # HSTS for production
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        return response

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Validate and sanitize incoming requests
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request body too large"
            )
        
        # Validate content type for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith(("application/json", "multipart/form-data")):
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Content-Type must be application/json or multipart/form-data"
                )
        
        # Log request details
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log response
        logger.info(
            f"Response: {response.status_code} in {process_time:.3f}s",
            extra={
                "status_code": response.status_code,
                "process_time": process_time,
                "path": request.url.path
            }
        )
        
        return response

class WebhookSignatureMiddleware:
    """
    Validate webhook signatures for external services
    """
    
    @staticmethod
    def verify_stripe_signature(payload: bytes, signature: str, secret: str) -> bool:
        """Verify Stripe webhook signature"""
        try:
            timestamp, signatures = signature.split(",")[0].split("=")[1], signature.split(",")[1].split("=")[1]
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            expected_signature = hmac.new(
                secret.encode("utf-8"),
                signed_payload.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected_signature, signatures)
        except Exception as e:
            logger.error(f"Stripe signature verification error: {str(e)}")
            return False
    
    @staticmethod
    def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
        """Verify GitHub webhook signature"""
        try:
            expected_signature = "sha256=" + hmac.new(
                secret.encode("utf-8"),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"GitHub signature verification error: {str(e)}")
            return False
