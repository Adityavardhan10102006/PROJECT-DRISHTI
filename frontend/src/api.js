/**
 * src/api.js — Project DRISHTI
 * ==============================
 * API client for FastAPI backend.
 * All fetch calls go through this module so the base URL is in one place.
 *
 * Authentication:
 *   - All protected endpoints include Authorization: Bearer <token>
 *   - 401 responses trigger automatic token clearing + redirect to login
 *   - Credentials (passwords) are NEVER logged or stored
 */

import { getToken, clearToken, setToken, authHeaders } from "./auth.js";

const API_BASE = import.meta.env.VITE_API_URL || "";

// ─────────────────────────────────────────────
// GLOBAL 401 HANDLER
// ─────────────────────────────────────────────

/**
 * Handle a 401 Unauthorized response globally.
 * Clears the stored token and notifies the app to redirect to login.
 * Uses a custom event so App.jsx can react without circular imports.
 */
function handle401() {
  clearToken();
  window.dispatchEvent(new CustomEvent("drishti:session-expired"));
}

// ─────────────────────────────────────────────
// CORE FETCH WRAPPER
// ─────────────────────────────────────────────

/**
 * Authenticated fetch wrapper.
 * Automatically injects Authorization header and handles 401 responses.
 *
 * @param {string} url
 * @param {RequestInit} options
 * @param {boolean} requireAuth - If true, 401 triggers session-expired event
 * @returns {Promise<Response>}
 */
async function apiFetch(url, options = {}, requireAuth = true) {
  const headers = {
    "Content-Type": "application/json",
    ...(requireAuth ? authHeaders() : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_BASE}${url}`, { ...options, headers });

  if (response.status === 401 && requireAuth) {
    handle401();
    throw new Error("Session expired. Please sign in again.");
  }

  return response;
}

// ─────────────────────────────────────────────
// AUTH ENDPOINTS
// ─────────────────────────────────────────────

/**
 * POST /auth/login — Authenticate and receive JWT access token.
 * @param {string} username
 * @param {string} password
 * @param {boolean} remember - Whether to persist session
 * @returns {Promise<{ access_token, token_type, expires_in, user }>}
 */
export async function login(username, password, remember = false) {
  const res = await apiFetch(
    "/auth/login",
    {
      method: "POST",
      body: JSON.stringify({ username, password }),
    },
    false, // Login endpoint doesn't require existing auth
  );

  if (!res.ok) {
    if (res.status === 429) {
      const err = await res.json().catch(() => ({ detail: "Too many login attempts. Try again later." }));
      throw new Error(err.detail || "Too many login attempts. Try again later.");
    }
    if (res.status === 401) {
      throw new Error("Invalid username or password.");
    }
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Login failed: ${res.status}`);
  }

  const data = await res.json();
  // Store token securely — NEVER store the password
  setToken(data.access_token, remember);
  return data;
}

/**
 * POST /auth/logout — Invalidate current session.
 * Clears token regardless of server response.
 */
export async function logout() {
  try {
    await apiFetch("/auth/logout", { method: "POST" }, true);
  } catch {
    // Always clear token on logout, even if server request fails
  } finally {
    clearToken();
  }
}

/**
 * GET /auth/verify — Check if the current token is still valid.
 * @returns {Promise<boolean>}
 */
export async function verifySession() {
  try {
    const token = getToken();
    if (!token) return false;
    const res = await apiFetch("/auth/verify", {}, true);
    return res.ok;
  } catch {
    return false;
  }
}

/**
 * GET /auth/me — Get current user info from backend.
 * @returns {Promise<{ authenticated, user: { username, role } }>}
 */
export async function fetchCurrentUser() {
  const res = await apiFetch("/auth/me", {}, true);
  if (!res.ok) throw new Error("Not authenticated");
  return res.json();
}

// ─────────────────────────────────────────────
// PROTECTED ENDPOINTS
// ─────────────────────────────────────────────

/**
 * POST /predict — submit a complaint and get predictions back.
 * @param {Object} payload  - { complaint_text, victim_lat?, victim_lon?, fraud_type?, amount?, ... }
 * @returns {Promise<Object>} - PredictionOut shape from backend
 */
export async function submitComplaint(payload) {
  const res = await apiFetch("/predict/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

/**
 * GET /health — check API + model status (public endpoint).
 * @returns {Promise<Object>} - HealthResponse shape
 */
export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

/**
 * POST /alerts/{id}/outcome — Log field operator outcome and update alert status
 */
export async function submitOutcomeFeedback(alertIdOrComplaintId, feedbackData) {
  const res = await apiFetch(
    `/alerts/${encodeURIComponent(alertIdOrComplaintId)}/outcome`,
    {
      method: "POST",
      body: JSON.stringify(feedbackData),
    },
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

/**
 * GET /alerts/feedback/stats — Retrieve accuracy & fund recovery statistics
 */
export async function fetchFeedbackStats() {
  const res = await fetch(`${API_BASE}/alerts/feedback/stats`);
  if (!res.ok) throw new Error(`Stats fetch failed: ${res.status}`);
  return res.json();
}

/**
 * POST /alerts/feedback/retrain — Trigger continuous retraining loop (API Key Protected)
 */
export async function triggerRetraining(apiKey = import.meta.env.VITE_ADMIN_API_KEY || "your-secure-key-here") {
  const res = await apiFetch("/alerts/feedback/retrain", {
    method: "POST",
    headers: {
      "X-API-Key": apiKey,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Retraining request failed: ${res.status}`);
  }
  return res.json();
}

/**
 * Real-Time Simulation Stream APIs
 */
export async function fetchSimStatus() {
  const res = await fetch(`${API_BASE}/api/simulation/status`);
  if (!res.ok) throw new Error(`Sim status failed: ${res.status}`);
  return res.json();
}

export async function startSimulation(intervalSeconds = 2.0) {
  const res = await apiFetch("/api/simulation/start", {
    method: "POST",
    body: JSON.stringify({ interval_seconds: intervalSeconds }),
  });
  if (!res.ok) throw new Error(`Sim start failed: ${res.status}`);
  return res.json();
}

export async function stopSimulation() {
  const res = await apiFetch("/api/simulation/stop", {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Sim stop failed: ${res.status}`);
  return res.json();
}
