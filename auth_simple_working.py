"""
Simple Working Authentication
No complexity, just works
"""

import os
import jwt
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configuration - Use same secret as auth_middleware for compatibility
import os
JWT_SECRET = os.getenv("JWT_SECRET", "commercial-grade-secret-key-2025")  # MUST match auth_middleware.py
JWT_ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Simple hash"""
    return hashlib.sha256(f"{password}salt2025".encode()).hexdigest()

def create_token(data: dict) -> str:
    """Create JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    """Verify JWT token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except:
        return None

def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Optional auth - returns None if no token"""
    if not credentials:
        return None

    payload = verify_token(credentials.credentials)
    if payload:
        return {"email": payload.get("email"), "user_id": payload.get("user_id")}
    return None

def get_current_user_required(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Required auth - raises error if no valid token"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {"email": payload.get("email"), "user_id": payload.get("user_id")}

# Test user creation for initialization
def create_test_users(db):
    """Create test users in database"""
    from sqlalchemy import text

    test_users = [
        {
            "id": str(uuid.uuid4()),
            "email": "admin@weathercraft.com",
            "password": hash_password("admin123"),
            "name": "Admin User",
            "role": "admin"
        },
        {
            "id": str(uuid.uuid4()),
            "email": "test@test.com",
            "password": hash_password("TestPassword123!"),
            "name": "Test User",
            "role": "user"
        },
        {
            "id": str(uuid.uuid4()),
            "email": "demo@myroofgenius.com",
            "password": hash_password("demo123"),
            "name": "Demo User",
            "role": "user"
        }
    ]

    try:
        for user in test_users:
            # Check if user exists
            result = db.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": user["email"]}
            ).first()

            if not result:
                # Create user
                db.execute(
                    text("""
                        INSERT INTO users (id, email, password, name, role, created_at)
                        VALUES (:id, :email, :password, :name, :role, NOW())
                        ON CONFLICT (email) DO NOTHING
                    """),
                    user
                )
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error creating test users: {e}")