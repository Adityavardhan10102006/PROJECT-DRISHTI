/**
 * src/auth.js — Project DRISHTI
 * ================================
 * Client-side authentication state management.
 *
 * Architecture:
 *   - JWT Bearer tokens from POST /auth/login
 *   - sessionStorage by default (cleared when tab/browser closes)
 *   - localStorage when "Remember Me" is checked (persistent)
 *   - Token decoded client-side only for display — validation is always server-side
 *   - No passwords, no hashes, no sensitive data ever stored
 *
 * Security:
 *   - Tokens stored only in browser storage (not cookies, no XSS-accessible meta)
 *   - No credentials ever stored
 *   - Expiry checked client-side for UX only — server validates on every request
 */

const TOKEN_KEY = "drishti_access_token";
const REMEMBER_KEY = "drishti_remember";

// ─────────────────────────────────────────────
// TOKEN STORAGE
// ─────────────────────────────────────────────

/**
 * Store the JWT access token.
 * @param {string} token   - The JWT string
 * @param {boolean} remember - If true, persist in localStorage; else sessionStorage
 */
export function setToken(token, remember = false) {
  if (remember) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(REMEMBER_KEY, "true");
    sessionStorage.removeItem(TOKEN_KEY);
  } else {
    sessionStorage.setItem(TOKEN_KEY, token);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REMEMBER_KEY);
  }
}

/**
 * Retrieve the stored JWT token.
 * Checks sessionStorage first, then localStorage (for remember-me sessions).
 * @returns {string|null}
 */
export function getToken() {
  return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY) || null;
}

/**
 * Remove the stored token from all storage locations.
 * Called on logout or session expiry.
 */
export function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REMEMBER_KEY);
}

// ─────────────────────────────────────────────
// TOKEN PARSING
// ─────────────────────────────────────────────

/**
 * Decode the JWT payload without verifying the signature.
 * Used CLIENT-SIDE ONLY for display purposes (username, role).
 * The signature is always verified server-side on protected API calls.
 *
 * @param {string} token
 * @returns {Object|null}
 */
function decodeTokenPayload(token) {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = parts[1];
    // Base64url → Base64 → JSON
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const json = atob(base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "="));
    return JSON.parse(json);
  } catch {
    return null;
  }
}

// ─────────────────────────────────────────────
// AUTH STATE
// ─────────────────────────────────────────────

/**
 * Check if the user is currently authenticated (has a non-expired token).
 * This is a CLIENT-SIDE check for UX only — the server validates on every request.
 * @returns {boolean}
 */
export function isAuthenticated() {
  const token = getToken();
  if (!token) return false;

  const payload = decodeTokenPayload(token);
  if (!payload) return false;

  // Check expiry (exp is Unix timestamp in seconds)
  if (payload.exp && Date.now() / 1000 > payload.exp) {
    clearToken(); // Auto-clear expired token
    return false;
  }

  return true;
}

/**
 * Get the current authenticated user info from the stored token.
 * @returns {{ username: string, role: string } | null}
 */
export function getUser() {
  const token = getToken();
  if (!token) return null;

  const payload = decodeTokenPayload(token);
  if (!payload) return null;

  return {
    username: payload.sub || "Unknown",
    role: payload.role || "analyst",
  };
}

/**
 * Get the number of seconds until the token expires.
 * @returns {number} seconds remaining, or 0 if expired/no token
 */
export function getTokenExpiresIn() {
  const token = getToken();
  if (!token) return 0;
  const payload = decodeTokenPayload(token);
  if (!payload?.exp) return 0;
  return Math.max(0, Math.floor(payload.exp - Date.now() / 1000));
}

// ─────────────────────────────────────────────
// AUTH HEADERS
// ─────────────────────────────────────────────

/**
 * Returns the Authorization header object for authenticated API requests.
 * @returns {Object} e.g. { "Authorization": "Bearer eyJ..." }
 */
export function authHeaders() {
  const token = getToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}
