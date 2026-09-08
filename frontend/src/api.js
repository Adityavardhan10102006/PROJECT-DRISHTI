/**
 * src/api.js — Project DRISHTI
 * API client for FastAPI backend.
 * All fetch calls go through this module so the base URL is in one place.
 *
 * Day 4: Replace with WebSocket subscription for real-time push.
 */

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * POST /predict — submit a complaint and get predictions back.
 * @param {Object} payload  - { complaint_text, victim_lat?, victim_lon?, fraud_type?, amount?, ... }
 * @returns {Promise<Object>} - PredictionOut shape from backend
 */
export async function submitComplaint(payload) {
  const res = await fetch(`${API_BASE}/predict/`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

/**
 * GET /health — check API + model status.
 * @returns {Promise<Object>} - HealthResponse shape
 */
export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

/**
 * POST /alerts/{id}/outcome — Log field operator outcome
 */
export async function submitOutcomeFeedback(complaintId, feedbackData) {
  const res = await fetch(`${API_BASE}/alerts/${encodeURIComponent(complaintId)}/outcome`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(feedbackData),
  });
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
 * POST /alerts/feedback/retrain — Trigger continuous retraining loop
 */
export async function triggerRetraining() {
  const res = await fetch(`${API_BASE}/alerts/feedback/retrain`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Retraining request failed: ${res.status}`);
  return res.json();
}

