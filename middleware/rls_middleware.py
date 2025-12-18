"""
Row Level Security Middleware
Automatically sets user context for database queries
"""

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text
import logging
from typing import Optional
from jose import JWTError, jwt
import os

logger = logging.getLogger(__name__)

# Configuration - SECURITY: JWT_SECRET_KEY must be set in production
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    # In development, warn but allow startup with a dev-only key
    if os.getenv("ENVIRONMENT", "development").lower() in ("development", "dev", "local"):
        logger.warning("⚠️ JWT_SECRET_KEY not set - using development fallback. DO NOT USE IN PRODUCTION!")
        SECRET_KEY = "dev-only-secret-key-min-32-chars-long-not-for-production"
    else:
        raise RuntimeError(
            "FATAL: JWT_SECRET_KEY environment variable must be set in production. "
            "Generate a secure key with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

class RLSMiddleware(BaseHTTPMiddleware):
    """Middleware to set RLS context for each request"""

    async def dispatch(self, request: Request, call_next):
        # Skip RLS for public endpoints
        public_paths = [
            "/api/v1/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]

        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)

        # Try to extract user from JWT token
        user_id = None
        user_role = None

        try:
            # Get authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

                # Decode token
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
                user_role = payload.get("role", "user")

                # Set RLS context in database
                if user_id and hasattr(request.app.state, "db"):
                    db = request.app.state.db
                    try:
                        # Set the current user context for RLS
                        db.execute(
                            text("SELECT set_config('app.current_user_id', :user_id, false)"),
                            {"user_id": user_id}
                        )
                        db.execute(
                            text("SELECT set_config('app.current_user_role', :role, false)"),
                            {"role": user_role}
                        )
                    except Exception as e:
                        logger.warning(f"Failed to set RLS context: {e}")

        except (JWTError, Exception) as e:
            logger.debug(f"No valid auth token in request: {e}")

        # Store user info in request state
        request.state.user_id = user_id
        request.state.user_role = user_role

        # Process request
        response = await call_next(request)

        # Clear RLS context after request (optional)
        if user_id and hasattr(request.app.state, "db"):
            try:
                db = request.app.state.db
                db.execute(text("SELECT set_config('app.current_user_id', '', false)"))
                db.execute(text("SELECT set_config('app.current_user_role', '', false)"))
            except:
                pass

        return response


class RLSContext:
    """Context manager for RLS operations"""

    def __init__(self, db_session, user_id: str, user_role: str = "user"):
        self.db = db_session
        self.user_id = user_id
        self.user_role = user_role

    def __enter__(self):
        """Set RLS context on enter"""
        try:
            self.db.execute(
                text("SELECT set_config('app.current_user_id', :user_id, false)"),
                {"user_id": self.user_id}
            )
            self.db.execute(
                text("SELECT set_config('app.current_user_role', :role, false)"),
                {"role": self.user_role}
            )
        except Exception as e:
            logger.error(f"Failed to set RLS context: {e}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clear RLS context on exit"""
        try:
            self.db.execute(text("SELECT set_config('app.current_user_id', '', false)"))
            self.db.execute(text("SELECT set_config('app.current_user_role', '', false)"))
        except:
            pass


def set_rls_context(db_session, user_id: str, user_role: str = "user"):
    """Helper function to set RLS context"""
    try:
        db_session.execute(
            text("SELECT set_config('app.current_user_id', :user_id, false)"),
            {"user_id": user_id}
        )
        db_session.execute(
            text("SELECT set_config('app.current_user_role', :role, false)"),
            {"role": user_role}
        )
        return True
    except Exception as e:
        logger.error(f"Failed to set RLS context: {e}")
        return False


def clear_rls_context(db_session):
    """Helper function to clear RLS context"""
    try:
        db_session.execute(text("SELECT set_config('app.current_user_id', '', false)"))
        db_session.execute(text("SELECT set_config('app.current_user_role', '', false)"))
        return True
    except Exception as e:
        logger.error(f"Failed to clear RLS context: {e}")
        return False


def bypass_rls(db_session):
    """Temporarily bypass RLS for admin operations"""
    try:
        # Set to superadmin to bypass all policies
        db_session.execute(
            text("SELECT set_config('app.current_user_role', 'superadmin', false)")
        )
        return True
    except Exception as e:
        logger.error(f"Failed to bypass RLS: {e}")
        return False


# Decorator for RLS-protected routes
def with_rls(user_id: str = None, role: str = "user"):
    """Decorator to automatically set RLS context for a route"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get database session from kwargs
            db = kwargs.get("db")
            if db and user_id:
                set_rls_context(db, user_id, role)
                try:
                    result = await func(*args, **kwargs)
                finally:
                    clear_rls_context(db)
                return result
            else:
                return await func(*args, **kwargs)
        return wrapper
    return decorator