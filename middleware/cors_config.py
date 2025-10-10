"""
CORS Configuration
Comprehensive Cross-Origin Resource Sharing setup for security
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import logging

logger = logging.getLogger(__name__)

class CORSConfig:
    """Centralized CORS configuration"""

    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.allowed_origins = self._get_allowed_origins()
        self.allowed_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
        self.allowed_headers = [
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Requested-With",
            "X-CSRF-Token",
            "X-API-Key",
            "X-Client-Id",
            "X-Request-Id"
        ]
        self.expose_headers = [
            "X-Total-Count",
            "X-Page-Count",
            "X-Current-Page",
            "X-Per-Page",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "Content-Range",
            "Link"
        ]
        self.allow_credentials = True
        self.max_age = 3600  # 1 hour

    def _get_allowed_origins(self) -> List[str]:
        """Get allowed origins based on environment"""

        # Base origins that are always allowed
        base_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8000",
            "http://localhost:8002",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000"
        ]

        # Production origins
        production_origins = [
            "https://weathercraft-erp.vercel.app",
            "https://weathercraft-app.vercel.app",
            "https://myroofgenius.com",
            "https://www.myroofgenius.com",
            "https://brainops-backend-prod.onrender.com",
            "https://brainops-task-os.vercel.app",
            "https://weathercraftroofingco.com",
            "https://www.weathercraftroofingco.com"
        ]

        # Staging/preview origins (Vercel preview deployments)
        staging_origins = [
            "https://weathercraft-erp-*.vercel.app",
            "https://weathercraft-app-*.vercel.app",
            "https://*-mwwoodworth.vercel.app"
        ]

        # Custom origins from environment variable
        custom_origins = os.getenv("CORS_ORIGINS", "").split(",")
        custom_origins = [origin.strip() for origin in custom_origins if origin.strip()]

        # Combine based on environment
        if self.environment == "production":
            allowed = production_origins + custom_origins
        elif self.environment == "staging":
            allowed = base_origins + production_origins + staging_origins + custom_origins
        else:  # development
            allowed = base_origins + production_origins + staging_origins + custom_origins

        # Remove duplicates while preserving order
        seen = set()
        unique_origins = []
        for origin in allowed:
            if origin not in seen:
                seen.add(origin)
                unique_origins.append(origin)

        return unique_origins

    def configure_cors(self, app: FastAPI) -> None:
        """Configure CORS middleware for FastAPI app"""

        logger.info(f"Configuring CORS for {self.environment} environment")
        logger.info(f"Allowed origins: {self.allowed_origins}")

        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.allowed_origins,
            allow_credentials=self.allow_credentials,
            allow_methods=self.allowed_methods,
            allow_headers=self.allowed_headers,
            expose_headers=self.expose_headers,
            max_age=self.max_age
        )

        # Add OPTIONS handler for preflight requests
        @app.options("/{full_path:path}")
        async def preflight_handler(full_path: str):
            """Handle preflight OPTIONS requests"""
            return {"message": "OK"}

    def is_origin_allowed(self, origin: str) -> bool:
        """Check if an origin is allowed"""
        if not origin:
            return False

        # Check exact match
        if origin in self.allowed_origins:
            return True

        # Check wildcard patterns (for staging)
        for allowed in self.allowed_origins:
            if "*" in allowed:
                # Convert wildcard pattern to regex
                import re
                pattern = allowed.replace("*", ".*")
                if re.match(f"^{pattern}$", origin):
                    return True

        return False

    def get_cors_headers(self, origin: str = None) -> dict:
        """Get CORS headers for manual response"""
        headers = {}

        if origin and self.is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin
        else:
            # Use first allowed origin as default
            headers["Access-Control-Allow-Origin"] = self.allowed_origins[0]

        headers["Access-Control-Allow-Credentials"] = str(self.allow_credentials).lower()
        headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
        headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
        headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)
        headers["Access-Control-Max-Age"] = str(self.max_age)

        return headers

# Singleton instance
cors_config = CORSConfig()

# Export convenience function
def setup_cors(app: FastAPI):
    """Setup CORS for FastAPI application"""
    cors_config.configure_cors(app)

    # Log configuration
    logger.info("CORS configuration completed")
    logger.info(f"Environment: {cors_config.environment}")
    logger.info(f"Total allowed origins: {len(cors_config.allowed_origins)}")

# Security headers middleware
async def add_security_headers(request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    # Only add HSTS in production
    if cors_config.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response