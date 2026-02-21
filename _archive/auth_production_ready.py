"""
Production-Ready Authentication System
Complete auth implementation that actually works
"""

import os
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
from passlib.context import CryptContext
import os
import jwt

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "production-secret-key-2025-weathercraft")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Security
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a password."""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict]:
    """Get current user from token (optional auth)"""
    if not credentials:
        return None

    try:
        payload = decode_token(credentials.credentials)
        return {
            "email": payload.get("email"),
            "user_id": payload.get("user_id"),
            "name": payload.get("name")
        }
    except HTTPException:
        return None

def require_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Require authenticated user (mandatory auth)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    return {
        "email": payload.get("email"),
        "user_id": payload.get("user_id"),
        "name": payload.get("name")
    }

def get_db():
    """Get database session"""
    from database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def authenticate_user(db: Session, email: str, password: str) -> Optional[Dict]:
    """Authenticate user with email and password securely."""
    try:
        query = text("""
            SELECT id, email, hashed_password, full_name as name
            FROM app_users
            WHERE email = :email
            LIMIT 1
        """)
        result = db.execute(query, {"email": email}).first()

        if not result:
            logger.warning(f"Authentication attempt for non-existent user: {email}")
            return None

        if not result.hashed_password or not verify_password(password, result.hashed_password):
            logger.warning(f"Invalid password for user: {email}")
            return None

        return {
            "id": str(result.id),
            "email": result.email,
            "name": result.name if result.name else email
        }

    except Exception as e:
        logger.error(f"Database error during authentication for {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during authentication.",
        )

def create_user(db: Session, email: str, password: str, name: str = None) -> Dict:
    """Create new user with a securely hashed password."""
    try:
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(password)

        query = text("""
            INSERT INTO app_users (id, email, hashed_password, full_name, created_at, is_active)
            VALUES (:id, :email, :hashed_password, :name, :created_at, :is_active)
            RETURNING id, email, full_name as name
        """)

        result = db.execute(query, {
            "id": user_id,
            "email": email,
            "hashed_password": hashed_password,
            "name": name or email,
            "created_at": datetime.utcnow(),
            "is_active": True
        })

        db.commit()
        user = result.first()

        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name
        }

    except Exception as e:
        logger.error(f"Create user error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user.",
        )

def init_default_users(db: Session):
    """Initialize default users for testing"""
    default_users = [
        ("admin@weathercraft.com", "admin123", "Admin User"),
        ("test@test.com", "TestPassword123!", "Test User"),
        ("demo@myroofgenius.com", "demo123", "Demo User"),
        ("matt@weathercraft.com", "password123", "Matt Woodworth"),
        ("sales@weathercraft.com", "sales123", "Sales Team"),
        ("support@weathercraft.com", "support123", "Support Team")
    ]

    for email, password, name in default_users:
        try:
            # Check if exists
            query = text("SELECT id FROM app_users WHERE email = :email")
            existing = db.execute(query, {"email": email}).first()

            if not existing:
                create_user(db, email, password, name)
                logger.info(f"Created default user: {email}")
        except Exception as e:
            logger.error(f"Error creating default user {email}: {e}")
            db.rollback()