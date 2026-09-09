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
    create_access_token,
    get_current_user,
)
from backend.services.authentication_service import get_auth_service

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
    Delegates validation, rate-limiting, authentication, and token issuance
    to the AuthenticationService facade.
    """
    client_ip = _get_client_ip(request)
    auth_service = get_auth_service()

    success, token_data, error_detail, status_code = auth_service.authenticate(
        username=body.username,
        password=body.password,
        client_ip=client_ip,
    )

    if not success or not token_data:
        raise HTTPException(
            status_code=status_code or status.HTTP_401_UNAUTHORIZED,
            detail=error_detail or "Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"} if status_code == 401 else None,
        )

    return TokenResponse(**token_data)


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
