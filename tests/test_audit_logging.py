"""
tests/test_audit_logging.py — Project DRISHTI
============================================
Tests for Security Audit Logs, RBAC enforcement, and data privacy.
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from backend.repositories.audit_repository import AuditRepository


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def admin_headers(client):
    res = client.post(
        "/auth/login",
        json={"username": "admin", "password": "Drishti@2026"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def analyst_headers(client):
    res = client.post(
        "/auth/login",
        json={"username": "analyst", "password": "Analyst@2026"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def investigator_headers(client):
    res = client.post(
        "/auth/login",
        json={"username": "investigator", "password": "Investigate@2026"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_audit_repository_logging():
    """Verify writing and querying entries directly via repository."""
    repo = AuditRepository()
    entry = repo.log(
        user="test_officer",
        action="CASE_INSPECTED",
        case_id="DR-TEST-99",
        result="SUCCESS",
        details={"ip": "127.0.0.1"},
    )
    assert entry.id is not None
    assert entry.user == "test_officer"
    assert entry.action == "CASE_INSPECTED"

    logs = repo.list_logs(case_id="DR-TEST-99")
    assert len(logs) >= 1
    assert logs[0].case_id == "DR-TEST-99"


def test_audit_logs_unauthenticated(client):
    """Unauthenticated access must be rejected with 401."""
    res = client.get("/audit-logs/")
    assert res.status_code == 401


def test_audit_logs_rbac_investigator_forbidden(client, investigator_headers):
    """Investigator role is forbidden from viewing system audit logs (403)."""
    res = client.get("/audit-logs/", headers=investigator_headers)
    assert res.status_code == 403
    assert "Forbidden" in res.json()["detail"]


def test_audit_logs_rbac_admin_and_analyst_allowed(client, admin_headers, analyst_headers):
    """Admin and Analyst roles are authorized to query audit logs (200)."""
    res_admin = client.get("/audit-logs/", headers=admin_headers)
    assert res_admin.status_code == 200
    assert isinstance(res_admin.json(), list)

    res_analyst = client.get("/audit-logs/", headers=analyst_headers)
    assert res_analyst.status_code == 200
    assert isinstance(res_analyst.json(), list)


def test_audit_logs_no_plaintext_passwords(client, admin_headers):
    """Audit logs must never store passwords or secrets in plain text."""
    res = client.get("/audit-logs/", headers=admin_headers)
    assert res.status_code == 200
    logs = res.json()
    for entry in logs:
        details_str = str(entry.get("details", ""))
        assert "Drishti@2026" not in details_str
        assert "password" not in details_str.lower() or "password_hash" not in details_str.lower()
