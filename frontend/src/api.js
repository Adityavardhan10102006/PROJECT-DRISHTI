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
// CORE FETCH WRAPPER WITH TIMEOUT & OFFLINE DETECTION
// ─────────────────────────────────────────────

export function getBackendBaseUrl() {
  return API_BASE || window.location.origin;
}

/**
 * Authenticated fetch wrapper.
 * Automatically injects Authorization header, handles 401 responses,
 * enforces a timeout via AbortController, and tracks backend availability.
 *
 * @param {string} url
 * @param {RequestInit} options
 * @param {boolean} requireAuth - If true, 401 triggers session-expired event
 * @param {number} timeoutMs - Request timeout in ms (default 12000)
 * @returns {Promise<Response>}
 */
async function apiFetch(url, options = {}, requireAuth = true, timeoutMs = 12000) {
  const headers = {
    "Content-Type": "application/json",
    ...(requireAuth ? authHeaders() : {}),
    ...(options.headers || {}),
  };

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE}${url}`, {
      ...options,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timer);

    // If request succeeded, notify that backend is reachable
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("drishti:network-online"));
    }

    if (response.status === 401 && requireAuth) {
      handle401();
      throw new Error("Session expired. Please sign in again.");
    }

    return response;
  } catch (err) {
    clearTimeout(timer);

    // Distinguish network connection failures from application errors
    if (err.name === "AbortError") {
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("drishti:network-offline", { detail: { reason: "timeout" } }));
      }
      throw new Error(`Request timed out after ${timeoutMs / 1000}s. Backend might be unreachable.`);
    }

    if (err instanceof TypeError && err.message.includes("fetch")) {
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("drishti:network-offline", { detail: { reason: "connection_refused" } }));
      }
      throw new Error("Cannot reach DRISHTI backend server. Please verify the service is running.");
    }

    throw err;
  }
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

// ─────────────────────────────────────────────
// CASE MANAGEMENT & INVESTIGATION APIS
// ─────────────────────────────────────────────

/**
 * GET /cases/stats — Retrieve Command Center KPI stats
 */
export async function fetchCaseStats() {
  const res = await apiFetch("/cases/stats");
  if (!res.ok) throw new Error(`Failed to fetch case stats: ${res.status}`);
  return res.json();
}

/**
 * GET /cases — Retrieve investigation cases list
 */
export async function fetchCases({ status, risk_level, search, limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams();
  if (status) params.append("status", status);
  if (risk_level) params.append("risk_level", risk_level);
  if (search) params.append("search", search);
  params.append("limit", limit.toString());
  params.append("offset", offset.toString());

  const res = await apiFetch(`/cases/?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to list cases: ${res.status}`);
  return res.json();
}

/**
 * GET /cases/{case_id} — Retrieve complete case dossier
 */
export async function fetchCaseDetail(caseId) {
  const res = await apiFetch(`/cases/${encodeURIComponent(caseId)}`);
  if (!res.ok) throw new Error(`Failed to load case ${caseId}: ${res.status}`);
  return res.json();
}

/**
 * GET /cases/{case_id}/timeline — Retrieve chronological timeline events
 */
export async function fetchCaseTimeline(caseId) {
  const res = await apiFetch(`/cases/${encodeURIComponent(caseId)}/timeline`);
  if (!res.ok) throw new Error(`Failed to load timeline: ${res.status}`);
  return res.json();
}

/**
 * PATCH /cases/{case_id}/status — Update case status
 */
export async function updateCaseStatus(caseId, status, note = null) {
  const res = await apiFetch(`/cases/${encodeURIComponent(caseId)}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status, note }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to update status: ${res.status}`);
  }
  return res.json();
}

/**
 * PATCH /cases/{case_id}/assign — Assign case to investigator
 */
export async function assignCaseInvestigator(caseId, investigator) {
  const res = await apiFetch(`/cases/${encodeURIComponent(caseId)}/assign`, {
    method: "PATCH",
    body: JSON.stringify({ investigator }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to assign case: ${res.status}`);
  }
  return res.json();
}

/**
 * POST /cases/{case_id}/outcome — Record field outcome and evaluate accuracy
 */
export async function recordCaseOutcome(caseId, outcomeData) {
  const res = await apiFetch(`/cases/${encodeURIComponent(caseId)}/outcome`, {
    method: "POST",
    body: JSON.stringify(outcomeData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to record outcome: ${res.status}`);
  }
  return res.json();
}

/**
 * POST /cases/candidate-retrain — Trigger candidate model validation & comparison
 */
export async function triggerCandidateRetrain() {
  const res = await apiFetch("/cases/candidate-retrain", {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Candidate retrain failed: ${res.status}`);
  }
  return res.json();
}

/**
 * GET /audit-logs — Retrieve system and investigator audit logs
 */
export async function fetchAuditLogs({ user, action, case_id, limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams();
  if (user) params.append("user", user);
  if (action) params.append("action", action);
  if (case_id) params.append("case_id", case_id);
  params.append("limit", limit.toString());
  params.append("offset", offset.toString());

  const res = await apiFetch(`/audit-logs/?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch audit logs: ${res.status}`);
  return res.json();
}

/**
 * GET /system/status — Full system status diagnostics matrix
 */
export async function fetchSystemStatus() {
  const res = await fetch(`${API_BASE}/system/status`);
  if (!res.ok) throw new Error(`System status failed: ${res.status}`);
  return res.json();
}

// ─────────────────────────────────────────────
// DATASETS & STORAGE
// ─────────────────────────────────────────────

/**
 * GET /datasets/ — List all registered datasets and telemetry
 */
export async function fetchDatasets() {
  const res = await apiFetch("/datasets/");
  if (!res.ok) throw new Error(`Failed to fetch datasets: ${res.status}`);
  return res.json();
}

/**
 * GET /datasets/{name}/sample — Fetch preview records and schema
 */
export async function fetchDatasetSample(name, limit = 30) {
  const res = await apiFetch(`/datasets/${encodeURIComponent(name)}/sample?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch dataset sample: ${res.status}`);
  return res.json();
}

/**
 * POST /datasets/validate — Run integrity validation
 */
export async function validateDatasets() {
  const res = await apiFetch("/datasets/validate", { method: "POST" });
  if (!res.ok) throw new Error(`Validation failed: ${res.status}`);
  return res.json();
}

/**
 * POST /datasets/generate — Trigger massive dataset generation
 */
export async function generateDatasets() {
  const res = await apiFetch("/datasets/generate", { method: "POST" });
  if (!res.ok) throw new Error(`Generation failed: ${res.status}`);
  return res.json();
}

// ─────────────────────────────────────────────
// TRANSACTIONS LEDGER
// ─────────────────────────────────────────────

/**
 * GET /transactions/ — Paginated, filterable financial transactions
 */
export async function fetchTransactions({
  case_id,
  account,
  transaction_type,
  is_fraud,
  min_amount,
  max_amount,
  search,
  limit = 50,
  offset = 0,
} = {}) {
  const params = new URLSearchParams();
  if (case_id) params.append("case_id", case_id);
  if (account) params.append("account", account);
  if (transaction_type) params.append("transaction_type", transaction_type);
  if (is_fraud !== undefined && is_fraud !== null && is_fraud !== "") params.append("is_fraud", is_fraud.toString());
  if (min_amount) params.append("min_amount", min_amount.toString());
  if (max_amount) params.append("max_amount", max_amount.toString());
  if (search) params.append("search", search);
  params.append("limit", limit.toString());
  params.append("offset", offset.toString());

  const res = await apiFetch(`/transactions/?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch transactions: ${res.status}`);
  return res.json();
}

/**
 * GET /transactions/stats — Financial ledger aggregates
 */
export async function fetchTransactionStats() {
  const res = await apiFetch("/transactions/stats");
  if (!res.ok) throw new Error(`Failed to fetch transaction stats: ${res.status}`);
  return res.json();
}

// ─────────────────────────────────────────────
// ANALYTICS & INTELLIGENCE REPORTS
// ─────────────────────────────────────────────

/**
 * GET /analytics/summary — Comprehensive chart metrics and trends
 */
export async function fetchAnalyticsSummary() {
  const res = await apiFetch("/analytics/summary");
  if (!res.ok) throw new Error(`Failed to fetch analytics summary: ${res.status}`);
  return res.json();
}

// ─────────────────────────────────────────────
// UNIVERSAL INTELLIGENCE SEARCH & PROSPECTS
// ─────────────────────────────────────────────

/**
 * GET /intelligence/search — Universal multi-entity investigative search
 */
export async function searchIntelligence({
  q = "",
  entity_type = "all",
  risk,
  fraud_type,
  city,
  bank,
  min_amount,
  max_amount,
  case_id,
  limit = 50,
  offset = 0,
} = {}) {
  const params = new URLSearchParams();
  if (q) params.append("q", q);
  if (entity_type) params.append("entity_type", entity_type);
  if (risk) params.append("risk", risk);
  if (fraud_type) params.append("fraud_type", fraud_type);
  if (city) params.append("city", city);
  if (bank) params.append("bank", bank);
  if (min_amount !== undefined && min_amount !== null && min_amount !== "") params.append("min_amount", min_amount.toString());
  if (max_amount !== undefined && max_amount !== null && max_amount !== "") params.append("max_amount", max_amount.toString());
  if (case_id) params.append("case_id", case_id);
  params.append("limit", limit.toString());
  params.append("offset", offset.toString());

  const res = await apiFetch(`/intelligence/search?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to execute intelligence search: ${res.status}`);
  return res.json();
}

/**
 * GET /atms/candidates — Transparent multi-factor candidate cash-out prospects
 */
export async function fetchCandidateProspects({
  case_id,
  victim_lat,
  victim_lon,
  amount,
  fraud_type,
  k = 6,
} = {}) {
  const params = new URLSearchParams();
  if (case_id) params.append("case_id", case_id);
  if (victim_lat !== undefined && victim_lat !== null) params.append("victim_lat", victim_lat.toString());
  if (victim_lon !== undefined && victim_lon !== null) params.append("victim_lon", victim_lon.toString());
  if (amount !== undefined && amount !== null) params.append("amount", amount.toString());
  if (fraud_type) params.append("fraud_type", fraud_type);
  params.append("k", k.toString());

  const res = await apiFetch(`/atms/candidates?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch cash-out candidates: ${res.status}`);
  return res.json();
}

// ─────────────────────────────────────────────
// INTEGRATION ARCHITECTURE & DATA SOURCES
// ─────────────────────────────────────────────

/**
 * GET /integration/sources — Honest listing of active prototype & institutional adapters
 */
export async function fetchIntegrationSources() {
  const res = await apiFetch("/integration/sources");
  if (!res.ok) throw new Error(`Failed to fetch integration sources: ${res.status}`);
  return res.json();
}

/**
 * GET /integration/provenance — Regulatory dataset provenance and boundary notice
 */
export async function fetchIntegrationProvenance() {
  const res = await apiFetch("/integration/provenance");
  if (!res.ok) throw new Error(`Failed to fetch provenance: ${res.status}`);
  return res.json();
}


