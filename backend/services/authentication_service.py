"""
backend/services/authentication_service.py — Project DRISHTI
============================================================
Object-Oriented Authentication & Identity Architecture.
Decomposes auth into PasswordHasher, SessionManager, and AuthenticationService facade.
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.repositories.user_repository import UserRepository
from backend.repositories.audit_repository import AuditRepository
from backend.auth.rate_limiter import is_locked_out, record_failure, record_success
from backend.auth.user_model import User


class PasswordHasher:
    """
    Encapsulates password hashing and constant-time verification.
    """

    DUMMY_HASH = "$2b$12$KIXWKqt3t7PChOrUfbKrXuFaK8e.Z6tWNKmjH/xUcfBp0Xfq7lC76"

    def __init__(self, rounds: int = 12):
        self._ctx = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=rounds,
        )

    def hash(self, plain_password: str) -> str:
        """Computes bcrypt hash."""
        return self._ctx.hash(plain_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Constant-time verification of password against bcrypt hash."""
        try:
            return self._ctx.verify(plain_password, hashed_password)
        except Exception:
            return False

    def dummy_verify(self) -> None:
        """Runs dummy check to prevent timing attacks that reveal user existence."""
        try:
            self._ctx.verify("dummy_timing_check", self.DUMMY_HASH)
        except Exception:
            pass


class SessionManager:
    """
    Encapsulates JWT token lifecycle, generation, expiration, and decoding.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        expiry_minutes: int = 30,
    ):
        self.secret_key = secret_key or os.getenv("DRISHTI_SECRET_KEY", "")
        if not self.secret_key:
            self.secret_key = secrets.token_hex(32)
        self.algorithm = algorithm
        self.expiry_minutes = int(os.getenv("SESSION_EXPIRY", str(expiry_minutes)))

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Creates signed JWT token with standard claims."""
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + (expires_delta if expires_delta else timedelta(minutes=self.expiry_minutes))
        to_encode.update({"exp": expire, "iat": now})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decodes and validates a JWT token. Raises JWTError on expiration/tampering."""
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])


class AuthenticationService:
    """
    Central Authentication Facade & Orchestrator.
    Demonstrates Dependency Injection by accepting repository, hasher, and session manager.
    """

    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        hasher: Optional[PasswordHasher] = None,
        session_mgr: Optional[SessionManager] = None,
        audit_repo: Optional[AuditRepository] = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.hasher = hasher or PasswordHasher()
        self.session_mgr = session_mgr or SessionManager()
        self.audit_repo = audit_repo or AuditRepository()

    def authenticate(
        self,
        username: str,
        password: str,
        client_ip: str = "127.0.0.1",
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str], Optional[int]]:
        """
        Validates credentials with brute-force rate limiting.

        Returns:
            (success, token_data, error_detail, http_status_code)
        """
        # 1. Rate-limit check
        if is_locked_out(client_ip):
            self.audit_repo.log(
                user=username or "UNKNOWN",
                action="USER_LOGIN_LOCKED",
                result="FAILURE",
                details={"client_ip": client_ip, "reason": "rate_limited"},
            )
            return (
                False,
                None,
                "Too many failed login attempts. Account temporarily locked. Please try again in 15 minutes.",
                429,
            )

        # 2. Lookup user
        user = self.user_repo.find_by_username_or_email(username)

        if user is None:
            self.hasher.dummy_verify()
            locked, _, retry_after = record_failure(client_ip)
            self.audit_repo.log(
                user=username or "UNKNOWN",
                action="USER_LOGIN_FAILED",
                result="FAILURE",
                details={"client_ip": client_ip, "reason": "user_not_found"},
            )
            if locked:
                return False, None, f"Too many failed login attempts. Account locked for {retry_after // 60} minutes.", 429
            return False, None, "Invalid username or password.", 401

        # 3. Verify password
        if not self.hasher.verify(password, user.password_hash):
            locked, _, retry_after = record_failure(client_ip)
            self.audit_repo.log(
                user=user.username,
                action="USER_LOGIN_FAILED",
                result="FAILURE",
                details={"client_ip": client_ip, "reason": "invalid_password"},
            )
            if locked:
                return False, None, f"Too many failed login attempts. Account locked for {retry_after // 60} minutes.", 429
            return False, None, "Invalid username or password.", 401

        # 4. Success — reset rate limiter & update last login
        record_success(client_ip)
        safe_user = self.user_repo.update_last_login(user.id) or user.to_safe_dict()

        # 5. Log audit trail
        self.audit_repo.log(
            user=user.username,
            action="USER_LOGIN",
            result="SUCCESS",
            details={"client_ip": client_ip, "role": user.role, "user_id": user.id},
        )
        print(f"[AUTH] Login successful: '{user.username}' (role: {user.role}) from {client_ip}")

        # 6. Issue JWT
        token_payload = {
            "sub": user.username,
            "role": user.role,
            "uid": user.id,
        }
        token = self.session_mgr.create_access_token(token_payload)

        return (
            True,
            {
                "access_token": token,
                "token_type": "bearer",
                "expires_in": self.session_mgr.expiry_minutes * 60,
                "user": safe_user,
            },
            None,
            200,
        )

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verifies JWT and returns payload if valid, None if invalid/expired."""
        try:
            return self.session_mgr.decode_token(token)
        except JWTError:
            return None


_auth_service_instance: Optional[AuthenticationService] = None

def get_auth_service() -> AuthenticationService:
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = AuthenticationService()
    return _auth_service_instance
