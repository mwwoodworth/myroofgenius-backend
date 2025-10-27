"""
Security middleware for rate limiting, API key validation, and request protection
"""

import time
import hashlib
import hmac
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
import redis
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import json

from app.core.config import settings
from app.core.exceptions import RateLimitError, AuthenticationError

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
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
    API key validation middleware
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.public_paths = [
            "/",
            "/health",
            "/api/v1/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip validation for public paths
        if any(request.url.path.startswith(path) for path in self.public_paths):
            return await call_next(request)
        
        # Check for API key
        api_key = self._extract_api_key(request)
        
        if api_key:
            db_pool = getattr(request.app.state, 'db_pool', None)

            if await self._validate_api_key(api_key, db_pool):
                # Add API key info to request state
                request.state.api_key = api_key
                request.state.authenticated = True
            else:
                raise AuthenticationError("Invalid API key")
        
        return await call_next(request)
    
    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request"""
        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        
        # Check X-API-Key header
        return request.headers.get("X-API-Key")
    
    async def _validate_api_key(self, api_key: str, db_pool) -> bool:
        """Validate API key against database"""
        if not api_key or len(api_key) < 16:
            return False

        if not db_pool:
            logger.error('Database pool unavailable for API key validation')
            return False

        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        try:
            async with db_pool.acquire() as conn:
                record = await conn.fetchrow(
                    """
                    SELECT id
                    FROM api_keys
                    WHERE key_hash = $1
                      AND (is_active IS NULL OR is_active = TRUE)
                      AND (expires_at IS NULL OR expires_at > NOW())
                    """,
                    key_hash
                )

                if not record:
                    return False

                await conn.execute(
                    """
                    UPDATE api_keys
                    SET last_used_at = NOW(),
                        usage_count = COALESCE(usage_count, 0) + 1
                    WHERE id = $1
                    """,
                    record['id']
                )

                return True
        except Exception as error:
            logger.error('API key validation error: %s', error)
            return False

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
