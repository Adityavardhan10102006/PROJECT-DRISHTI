"""
backend/routes/auth.py — Project DRISHTI
==========================================
Authentication endpoints:

  POST /auth/login    — Validate credentials, return JWT access token
  POST /auth/logout   — Client-side token invalidation (stateless)
  GET  /auth/me       — Return current authenticated user info
  GET  /auth/verify   — Lightweight token validity check

Security:
  - bcrypt password verification (constant-time)
  - Generic error messages (never reveals whether username exists)
  - Rate limiting: 5 failures per IP → 15-minute lockout (429)
  - No sensitive info in JWT payload (no password, no hash)
  - last_login timestamp updated on successful auth
"""

from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request, status
from fastapi import Depends
from pydantic import BaseModel, Field

from backend.auth.security import (
    verify_password,
    create_access_token,
    get_current_user,
)
from backend.auth.rate_limiter import (
    is_locked_out,
    record_failure,
    record_success,
)
from backend.database import SessionLocal
from backend.auth.user_model import User

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ─────────────────────────────────────────────
# REQUEST / RESPONSE SCHEMAS
# ─────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64, description="Username or email")
    password: str = Field(..., min_length=1, max_length=256, description="Account password")

    model_config = {"json_schema_extra": {"example": {"username": "admin", "password": "Drishti@2026"}}}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: dict       # Safe user info (no password_hash)


class MessageResponse(BaseModel):
    message: str
    authenticated: bool = False


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid username or password.",
    headers={"WWW-Authenticate": "Bearer"},
)

_GENERIC_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid username or password.",
    headers={"WWW-Authenticate": "Bearer"},
)


def _get_client_ip(request: Request) -> str:
    """Extract the real client IP, respecting X-Forwarded-For if behind proxy."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _authenticate_user(db, username: str, password: str) -> Optional[User]:
    """
    Lookup user by username and verify password.
    Returns User on success, None on failure.
    Does NOT reveal which field failed — always constant-time.
    """
    # Try username match first, then email
    user: Optional[User] = (
        db.query(User)
        .filter(
            (User.username == username.strip().lower()) |
            (User.email == username.strip().lower()),
            User.is_active == True,
        )
        .first()
    )

    if user is None:
        # Still run hash to prevent timing attacks revealing non-existence
        verify_password("dummy_check", "$2b$12$KIXWKqt3t7PChOrUfbKrXuFaK8e.Z6tWNKmjH/xUcfBp0Xfq7lC76")
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive JWT access token",
    responses={
        200: {"description": "Login successful — returns JWT access token"},
        401: {"description": "Invalid credentials"},
        429: {"description": "Too many failed attempts — account temporarily locked"},
    },
)
async def login(request: Request, body: LoginRequest) -> TokenResponse:
    """
    Authenticate with username/password. Returns a signed JWT access token.

    - Token expires in SESSION_EXPIRY (default: 30 minutes)
    - Rate limited: 5 failures per IP → 15-minute lockout
    - Generic error messages — does NOT reveal whether username exists
    - Password verification is constant-time (bcrypt)
    """
    client_ip = _get_client_ip(request)
    identifier = client_ip  # Rate limit by IP

    # ── 1. Rate limit check ──────────────────────────
    if is_locked_out(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Too many failed login attempts. "
                "Account temporarily locked. Please try again in 15 minutes."
            ),
        )

    # ── 2. Validate credentials ───────────────────────
    db = SessionLocal()
    try:
        user = _authenticate_user(db, body.username, body.password)
    finally:
        db.close()

    if not user:
        locked, failures, retry_after = record_failure(identifier)
        if locked:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Too many failed login attempts. "
                    f"Account temporarily locked for {retry_after // 60} minutes."
                ),
            )
        # Generic message — don't reveal which field was wrong
        raise _INVALID_CREDENTIALS

    # ── 3. Login successful — clear rate limit ────────
    record_success(identifier)

    # ── 4. Update last_login timestamp ───────────────
    db = SessionLocal()
    try:
        user_record = db.query(User).filter(User.id == user.id).first()
        if user_record:
            user_record.last_login = datetime.now(timezone.utc)
            db.commit()
            db.refresh(user_record)
            safe_user = user_record.to_safe_dict()
    except Exception:
        safe_user = user.to_safe_dict()
    finally:
        db.close()

    # ── 5. Create JWT ─────────────────────────────────
    import os
    expiry_minutes = int(os.getenv("SESSION_EXPIRY", "30"))
    token_payload = {
        "sub": user.username,
        "role": user.role,
        "uid": user.id,
    }
    access_token = create_access_token(token_payload)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expiry_minutes * 60,
        user=safe_user,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout — invalidates client-side token",
)
async def logout(current_user: dict = Depends(get_current_user)) -> MessageResponse:
    """
    Logout endpoint. Since JWTs are stateless, the client MUST discard the token.
    This endpoint confirms the token was valid at logout time.

    After calling this, the frontend clears its stored token.
    Any subsequent requests with the old token will fail once it expires.
    """
    return MessageResponse(
        message=f"Logged out successfully. Goodbye, {current_user.get('sub', 'user')}.",
        authenticated=False,
    )


@router.get(
    "/me",
    summary="Get current authenticated user info",
    responses={
        200: {"description": "Current user information (no password)"},
        401: {"description": "Not authenticated"},
    },
)
async def get_me(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Return information about the currently authenticated user.
    Never returns password_hash or any sensitive credential.
    """
    return {
        "authenticated": True,
        "user": {
            "username": current_user.get("sub"),
            "role": current_user.get("role", "analyst"),
        },
    }


@router.get(
    "/verify",
    summary="Verify token validity",
    responses={
        200: {"description": "Token is valid"},
        401: {"description": "Token is invalid or expired"},
    },
)
async def verify_token(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Lightweight endpoint for the frontend to check if the stored token is still valid.
    Returns 200 if valid, 401 if expired or malformed.
    """
    return {
        "valid": True,
        "username": current_user.get("sub"),
        "role": current_user.get("role", "analyst"),
    }
