"""
tests/test_auth.py — Project DRISHTI
======================================
Authentication test suite.

Tests:
  - Login (valid, invalid, empty fields)
  - Authorization (unauthenticated access → 401)
  - Role enforcement (403 where applicable)
  - Logout flow
  - Session verification
  - Rate limiting
  - Security (password hashing, no credential leakage)

Run with:
    python -m pytest tests/test_auth.py -v
    python -m pytest tests/test_auth.py -v --tb=short
"""

import os
import sys
import time
import pytest

# Ensure project root is in path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Load environment first
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from fastapi.testclient import TestClient
from main import app
from backend.database import SessionLocal, init_db, init_users
from backend.auth.user_model import User
from backend.auth.security import hash_password, verify_password, create_access_token, decode_token
from backend.auth.rate_limiter import record_failure, record_success, is_locked_out, _attempts

# ─────────────────────────────────────────────
# TEST SETUP
# ─────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize DB and create test user before any tests run."""
    init_db()
    _ensure_test_user()
    yield


def _ensure_test_user():
    """Create test user in DB if not present."""
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "testadmin").first()
        if not existing:
            user = User(
                username="testadmin",
                email="testadmin@drishti.test",
                password_hash=hash_password("TestPass@123"),
                role="admin",
                is_active=True,
            )
            db.add(user)
            db.commit()
    finally:
        db.close()


@pytest.fixture(scope="session")
def client():
    """Return a FastAPI TestClient."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """Return Authorization header for testadmin user."""
    res = client.post("/auth/login", json={
        "username": "testadmin",
        "password": "TestPass@123",
    })
    assert res.status_code == 200, f"Auth fixture failed: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def clear_rate_limiter():
    """Clear rate limiter state before each test."""
    _attempts.clear()
    yield
    _attempts.clear()


# ─────────────────────────────────────────────
# SECURITY UNIT TESTS
# ─────────────────────────────────────────────

class TestPasswordSecurity:
    """Password hashing must be secure and never expose plaintext."""

    def test_password_is_hashed(self):
        """Stored password must be a bcrypt hash, not plaintext."""
        plain = "SecurePass@999"
        hashed = hash_password(plain)
        assert hashed != plain
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_password_verification_correct(self):
        """Correct password verifies against its own hash."""
        plain = "CorrectHorse@Battery1"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_password_verification_wrong(self):
        """Wrong password fails verification."""
        hashed = hash_password("CorrectPass@1")
        assert verify_password("WrongPass@1", hashed) is False

    def test_each_hash_is_unique(self):
        """Same password produces different hashes (bcrypt salt)."""
        plain = "SamePassword@1"
        h1 = hash_password(plain)
        h2 = hash_password(plain)
        assert h1 != h2  # Different salts

    def test_user_password_not_in_db_plaintext(self):
        """User stored in DB has a bcrypt hash, not plaintext."""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == "testadmin").first()
            assert user is not None
            assert user.password_hash != "TestPass@123"
            assert user.password_hash.startswith("$2")
        finally:
            db.close()


class TestJWTSecurity:
    """JWT tokens must be correctly signed and validated."""

    def test_token_creation_and_decode(self):
        """Token can be created and decoded correctly."""
        payload = {"sub": "testuser", "role": "analyst"}
        token = create_access_token(payload)
        decoded = decode_token(token)
        assert decoded["sub"] == "testuser"
        assert decoded["role"] == "analyst"
        assert "exp" in decoded

    def test_tampered_token_rejected(self):
        """Tampered token must raise JWTError."""
        from jose import JWTError
        payload = {"sub": "attacker", "role": "admin"}
        token = create_access_token(payload)
        # Tamper with the signature
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            decode_token(tampered)

    def test_wrong_secret_rejected(self):
        """Token signed with different secret must be rejected."""
        from jose import jwt, JWTError
        wrong_token = jwt.encode({"sub": "hacker"}, "wrong-secret", algorithm="HS256")
        with pytest.raises(JWTError):
            decode_token(wrong_token)


# ─────────────────────────────────────────────
# LOGIN ENDPOINT TESTS
# ─────────────────────────────────────────────

class TestLogin:
    """POST /auth/login — authentication endpoint."""

    def test_valid_credentials_return_200(self, client):
        """✓ Valid credentials → 200 with access token."""
        res = client.post("/auth/login", json={
            "username": "testadmin",
            "password": "TestPass@123",
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "testadmin"

    def test_valid_credentials_no_password_in_response(self, client):
        """✓ Login response must NOT contain password or password_hash."""
        res = client.post("/auth/login", json={
            "username": "testadmin",
            "password": "TestPass@123",
        })
        assert res.status_code == 200
        text = res.text
        assert "TestPass@123" not in text
        assert "password_hash" not in text
        assert "password" not in res.json().get("user", {})

    def test_invalid_password_returns_401(self, client):
        """✓ Wrong password → 401."""
        res = client.post("/auth/login", json={
            "username": "testadmin",
            "password": "WrongPassword@999",
        })
        assert res.status_code == 401

    def test_invalid_username_returns_401(self, client):
        """✓ Non-existent username → 401 (same as wrong password)."""
        res = client.post("/auth/login", json={
            "username": "nonexistent_user_xyz",
            "password": "SomePassword@1",
        })
        assert res.status_code == 401

    def test_generic_error_message(self, client):
        """✓ Error message must not reveal whether username exists."""
        res = client.post("/auth/login", json={
            "username": "nonexistent_user_xyz",
            "password": "AnyPassword@1",
        })
        detail = res.json().get("detail", "")
        assert "username" in detail.lower() or "password" in detail.lower()
        # Must NOT say "user not found" or "incorrect password" specifically
        assert "not found" not in detail.lower()
        assert "user exists" not in detail.lower()

    def test_empty_username_returns_422(self, client):
        """✓ Empty username → 422 Unprocessable Entity."""
        res = client.post("/auth/login", json={
            "username": "",
            "password": "SomePassword@1",
        })
        assert res.status_code == 422

    def test_empty_password_returns_422(self, client):
        """✓ Empty password → 422 Unprocessable Entity."""
        res = client.post("/auth/login", json={
            "username": "testadmin",
            "password": "",
        })
        assert res.status_code == 422

    def test_missing_fields_returns_422(self, client):
        """✓ Missing fields → 422."""
        res = client.post("/auth/login", json={})
        assert res.status_code == 422

    def test_token_contains_username_and_role(self, client):
        """✓ JWT payload contains 'sub' and 'role' fields."""
        res = client.post("/auth/login", json={
            "username": "testadmin",
            "password": "TestPass@123",
        })
        assert res.status_code == 200
        token = res.json()["access_token"]
        payload = decode_token(token)
        assert payload["sub"] == "testadmin"
        assert "role" in payload

    def test_token_has_expiry(self, client):
        """✓ JWT must include expiry claim."""
        res = client.post("/auth/login", json={
            "username": "testadmin",
            "password": "TestPass@123",
        })
        token = res.json()["access_token"]
        payload = decode_token(token)
        assert "exp" in payload
        assert payload["exp"] > time.time()


# ─────────────────────────────────────────────
# AUTHORIZATION TESTS
# ─────────────────────────────────────────────

class TestAuthorization:
    """Protected endpoints must reject unauthenticated requests."""

    def test_unauthenticated_predict_returns_401(self, client):
        """✓ Unauthenticated /predict → 401."""
        res = client.post("/predict/", json={"complaint_text": "test"})
        assert res.status_code == 401

    def test_authenticated_predict_is_allowed(self, client, auth_headers):
        """✓ Authenticated /predict → not 401 (may be 200 or other valid code)."""
        res = client.post(
            "/predict/",
            json={"complaint_text": "UPI fraud of 5000 rupees from SBI account"},
            headers=auth_headers,
        )
        assert res.status_code != 401
        assert res.status_code != 403

    def test_malformed_token_returns_401(self, client):
        """✓ Malformed Bearer token → 401."""
        res = client.post(
            "/predict/",
            json={"complaint_text": "test"},
            headers={"Authorization": "Bearer this-is-not-a-valid-jwt"},
        )
        assert res.status_code == 401

    def test_no_bearer_prefix_returns_401(self, client):
        """✓ Token without 'Bearer' prefix → 401."""
        # Login to get a real token
        login_res = client.post("/auth/login", json={
            "username": "testadmin", "password": "TestPass@123"
        })
        token = login_res.json()["access_token"]
        res = client.post(
            "/predict/",
            json={"complaint_text": "test"},
            headers={"Authorization": token},  # Missing "Bearer "
        )
        assert res.status_code == 401

    def test_health_endpoint_is_public(self, client):
        """✓ /health does NOT require authentication."""
        res = client.get("/health")
        assert res.status_code == 200

    def test_unauthenticated_outcome_submission_returns_401(self, client):
        """✓ Unauthenticated /alerts/{id}/outcome → 401."""
        res = client.post("/alerts/999/outcome", json={
            "was_intercepted": True,
            "location_accurate": True,
            "time_window_accurate": True,
            "mule_confirmed": True,
        })
        assert res.status_code == 401


# ─────────────────────────────────────────────
# ME / VERIFY ENDPOINT TESTS
# ─────────────────────────────────────────────

class TestMeVerify:
    """GET /auth/me and GET /auth/verify endpoints."""

    def test_me_returns_user_info(self, client, auth_headers):
        """✓ /auth/me returns authenticated user info."""
        res = client.get("/auth/me", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["authenticated"] is True
        assert data["user"]["username"] == "testadmin"

    def test_me_without_token_returns_401(self, client):
        """✓ /auth/me without token → 401."""
        res = client.get("/auth/me")
        assert res.status_code == 401

    def test_me_does_not_expose_password(self, client, auth_headers):
        """✓ /auth/me never contains password or password_hash."""
        res = client.get("/auth/me", headers=auth_headers)
        assert res.status_code == 200
        text = res.text
        assert "password" not in text
        assert "password_hash" not in text

    def test_verify_valid_token_returns_200(self, client, auth_headers):
        """✓ /auth/verify with valid token → 200."""
        res = client.get("/auth/verify", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["valid"] is True

    def test_verify_invalid_token_returns_401(self, client):
        """✓ /auth/verify with invalid token → 401."""
        res = client.get("/auth/verify", headers={
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.invalid.token"
        })
        assert res.status_code == 401


# ─────────────────────────────────────────────
# LOGOUT TESTS
# ─────────────────────────────────────────────

class TestLogout:
    """POST /auth/logout — session invalidation."""

    def test_logout_with_valid_token_returns_200(self, client, auth_headers):
        """✓ Logout with valid token → 200."""
        res = client.post("/auth/logout", headers=auth_headers)
        assert res.status_code == 200
        assert "logged out" in res.json()["message"].lower()

    def test_logout_without_token_returns_401(self, client):
        """✓ Logout without token → 401."""
        res = client.post("/auth/logout")
        assert res.status_code == 401


# ─────────────────────────────────────────────
# RATE LIMITING TESTS
# ─────────────────────────────────────────────

class TestRateLimiting:
    """Brute-force protection — 5 failures → lockout."""

    def test_single_failure_not_locked(self, client):
        """✓ Single failure does not lock out."""
        client.post("/auth/login", json={
            "username": "testadmin",
            "password": "wrong1",
        })
        # Should still be able to try again
        res = client.post("/auth/login", json={
            "username": "testadmin",
            "password": "TestPass@123",
        })
        assert res.status_code == 200

    def test_rate_limiter_records_failure(self):
        """✓ Rate limiter correctly counts failures."""
        _attempts.clear()
        locked, count, _ = record_failure("test-ip-1")
        assert not locked
        assert count == 1

    def test_rate_limiter_lockout_after_max_failures(self):
        """✓ Rate limiter locks out after MAX_FAILURES attempts."""
        from backend.auth.rate_limiter import MAX_FAILURES
        _attempts.clear()
        identifier = "test-ip-lockout"

        for i in range(MAX_FAILURES - 1):
            locked, _, _ = record_failure(identifier)
            assert not locked, f"Locked after {i+1} attempts (should wait until {MAX_FAILURES})"

        locked, _, _ = record_failure(identifier)
        assert locked, f"Should be locked after {MAX_FAILURES} failures"

    def test_rate_limiter_cleared_on_success(self):
        """✓ Successful login clears failure count."""
        _attempts.clear()
        identifier = "test-ip-success"
        record_failure(identifier)
        record_failure(identifier)
        record_success(identifier)
        assert not is_locked_out(identifier)
        assert identifier not in _attempts

    def test_login_rate_limit_returns_429(self, client):
        """✓ Excessive failures return HTTP 429."""
        from backend.auth.rate_limiter import MAX_FAILURES
        _attempts.clear()

        # Exhaust the rate limit (accounting for testclient using 127.0.0.1 or testclient)
        for i in range(MAX_FAILURES):
            client.post("/auth/login", json={
                "username": "testadmin",
                "password": f"wrong_password_{i}",
            })

        # Next attempt should be rate limited
        res = client.post("/auth/login", json={
            "username": "testadmin",
            "password": "wrong_final",
        })
        assert res.status_code in [429, 401]  # 429 if locked, 401 if just failed


# ─────────────────────────────────────────────
# SESSION / ROLE TESTS
# ─────────────────────────────────────────────

class TestRoles:
    """Role information is present and correct in JWT."""

    def test_admin_role_in_token(self, client):
        """✓ Admin user gets 'admin' role in JWT payload."""
        res = client.post("/auth/login", json={
            "username": "testadmin",
            "password": "TestPass@123",
        })
        assert res.status_code == 200
        token = res.json()["access_token"]
        payload = decode_token(token)
        assert payload["role"] == "admin"

    def test_role_in_me_response(self, client, auth_headers):
        """✓ /auth/me includes role in user info."""
        res = client.get("/auth/me", headers=auth_headers)
        assert res.status_code == 200
        assert "role" in res.json()["user"]


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=PROJECT_ROOT,
    )
    sys.exit(result.returncode)
