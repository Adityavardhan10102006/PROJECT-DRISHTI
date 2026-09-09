"""
backend/auth/security.py — Project DRISHTI
==========================================
JWT-based authentication using python-jose + passlib[bcrypt].

Provides:
  - Password hashing and verification (bcrypt)
  - JWT access token creation and verification
  - FastAPI dependency for authenticated routes (get_current_user)
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

load_dotenv()

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

SECRET_KEY: str = os.getenv("DRISHTI_SECRET_KEY", "")
if not SECRET_KEY:
    # Generate a temporary secret for dev if not set — warn loudly
    SECRET_KEY = secrets.token_hex(32)
    print(
        "[DRISHTI-AUTH] WARNING: DRISHTI_SECRET_KEY not set in .env. "
        "Using a temporary random key — sessions will not persist across restarts. "
        "Set DRISHTI_SECRET_KEY in your .env for production."
    )

ALGORITHM = "HS256"
SESSION_EXPIRY_MINUTES: int = int(os.getenv("SESSION_EXPIRY", "30"))

# ─────────────────────────────────────────────
# PASSWORD HASHING
# ─────────────────────────────────────────────

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # OWASP minimum; comfortable on modern hardware
)


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash. Constant-time safe."""
    return pwd_context.verify(plain_password, hashed_password)


# ─────────────────────────────────────────────
# JWT TOKENS
# ─────────────────────────────────────────────

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        data:          Payload to encode (should include 'sub', 'role')
        expires_delta: Override token lifetime (defaults to SESSION_EXPIRY_MINUTES)

    Returns:
        Signed JWT string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=SESSION_EXPIRY_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.

    Returns:
        Decoded payload dict

    Raises:
        JWTError if token is invalid or expired
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# ─────────────────────────────────────────────
# FASTAPI AUTH DEPENDENCY
# ─────────────────────────────────────────────

_bearer_scheme = HTTPBearer(auto_error=False)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired authentication credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> dict:
    """
    FastAPI dependency that validates the Bearer token and returns the user payload.

    Usage:
        @router.post("/some-protected-route")
        async def handler(current_user: dict = Depends(get_current_user)):
            ...

    Returns:
        dict with 'sub' (username), 'role', 'exp', 'iat'

    Raises:
        401 if no token or token is invalid/expired
    """
    if not credentials:
        raise _CREDENTIALS_EXCEPTION

    token = credentials.credentials
    try:
        payload = decode_token(token)
        username: Optional[str] = payload.get("sub")
        if not username:
            raise _CREDENTIALS_EXCEPTION
        return payload
    except JWTError:
        raise _CREDENTIALS_EXCEPTION


async def require_role(required_role: str):
    """
    Factory for role-based access control dependencies.

    Usage:
        @router.post("/admin-only")
        async def handler(user = Depends(require_role("admin"))):
            ...
    """
    async def _check_role(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", "analyst")
        # Role hierarchy: admin > analyst > investigator
        role_levels = {"admin": 3, "analyst": 2, "investigator": 1}
        user_level = role_levels.get(user_role, 0)
        required_level = role_levels.get(required_role, 99)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}.",
            )
        return current_user
    return _check_role
