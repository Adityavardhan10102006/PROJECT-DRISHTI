/**
 * src/LoginPage.jsx — Project DRISHTI Authentication UI
 * =======================================================
 * Professional cybersecurity / intelligence platform login page.
 *
 * Features:
 *   - Backend-validated JWT authentication
 *   - Password visibility toggle (accessible)
 *   - Remember Me (persistent session)
 *   - Loading state prevents double submission
 *   - Session-expired banner
 *   - Keyboard accessible (Enter to submit, proper labels)
 *   - Generic error messages (never reveals if username exists)
 *   - "Forgot Password" → admin-managed procedure (no fake email)
 *   - Matches DRISHTI design system
 *
 * Security:
 *   - Passwords are NEVER logged or stored
 *   - Token stored in auth.js (sessionStorage or localStorage)
 *   - No credentials in component state after successful login
 */

import { useState, useEffect, useRef } from "react";
import "./LoginPage.css";
import { login } from "./api.js";
import GarudaDrishtiIcon from "./components/GarudaDrishtiIcon.jsx";

// ─────────────────────────────────────────────
// ICONS (inline SVG — no external deps)
// ─────────────────────────────────────────────

function EyeIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
      <circle cx="12" cy="12" r="3"/>
    </svg>
  );
}

function EyeOffIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
      <line x1="1" y1="1" x2="23" y2="23"/>
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
      stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
    </svg>
  );
}

function AlertIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="8" x2="12" y2="12"/>
      <line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true">
      <polyline points="20 6 9 17 4 12"/>
    </svg>
  );
}

// ─────────────────────────────────────────────
// FORGOT PASSWORD MODAL
// ─────────────────────────────────────────────

function ForgotPasswordModal({ onClose }) {
  return (
    <div
      className="login-page"
      style={{ position: "fixed", inset: 0, zIndex: 200, background: "rgba(8,12,24,0.85)" }}
      onClick={onClose}
    >
      <div
        className="login-card"
        style={{ maxWidth: 380 }}
        onClick={e => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="forgot-title"
      >
        <div className="login-header">
          <div className="login-logo-row">
            <ShieldIcon />
            <span className="login-logo-text" style={{ fontSize: 20 }}>
              PASSWORD RESET
            </span>
          </div>
        </div>
        <div className="login-body">
          <p className="login-forgot-info" id="forgot-title">
            Password reset is managed by the system administrator.
          </p>
          <p className="login-forgot-info" style={{ marginTop: 12, color: "var(--text-muted)" }}>
            To reset your password, contact your DRISHTI system administrator or run the following command on the server:
          </p>
          <pre style={{
            marginTop: 12,
            background: "var(--bg-elevated)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-sm)",
            padding: "10px 12px",
            fontSize: 11,
            color: "var(--accent)",
            fontFamily: "monospace",
            overflowX: "auto",
          }}>
            python -m backend.auth.reset_password
          </pre>
          <button
            className="login-btn"
            style={{ marginTop: 20 }}
            onClick={onClose}
          >
            Close
          </button>
        </div>
        <div className="login-card-stripe" />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// MAIN LOGIN PAGE COMPONENT
// ─────────────────────────────────────────────

/**
 * @param {Object} props
 * @param {Function} props.onLogin - Called after successful login with user info
 * @param {boolean} props.sessionExpired - Show "session expired" banner
 */
export default function LoginPage({ onLogin, sessionExpired = false }) {
  const [username, setUsername]     = useState("");
  const [password, setPassword]     = useState("");
  const [remember, setRemember]     = useState(false);
  const [showPw, setShowPw]         = useState(false);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState(null);
  const [success, setSuccess]       = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [apiStatus, setApiStatus]   = useState("check"); // "ok" | "error" | "check"

  const usernameRef = useRef(null);

  // Auto-focus username field on mount
  useEffect(() => {
    usernameRef.current?.focus();
  }, []);

  // Check backend health for status indicator
  useEffect(() => {
    const controller = new AbortController();
    fetch("/health", { signal: controller.signal })
      .then(r => setApiStatus(r.ok ? "ok" : "error"))
      .catch(() => setApiStatus("error"));
    return () => controller.abort();
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();

    // Validate inputs client-side
    if (!username.trim()) {
      setError("Username is required.");
      usernameRef.current?.focus();
      return;
    }
    if (!password) {
      setError("Password is required.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await login(username.trim(), password, remember);
      // Clear password from state immediately after use
      setPassword("");
      setSuccess(true);

      // Brief success feedback before navigating
      setTimeout(() => {
        onLogin(data.user);
      }, 600);
    } catch (err) {
      setError(err.message || "Sign in failed. Please try again.");
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter") handleSubmit(e);
  }

  return (
    <>
      <div className="login-page" role="main" aria-label="DRISHTI Authentication">
        {/* Decorative background */}
        <div className="login-bg-grid" aria-hidden="true" />
        <div className="login-bg-glow" aria-hidden="true" />
        <div className="login-corner login-corner-tl" aria-hidden="true" />
        <div className="login-corner login-corner-br" aria-hidden="true" />

        <div className="login-card">
          {/* ── HEADER ──────────────────────────────────────── */}
          <div className="login-header">
            <div className="login-logo-row">
              <GarudaDrishtiIcon size={44} glow />
              <h1 className="login-logo-text">DRISHTI</h1>
            </div>

            <p className="login-tagline">
              Predictive Cybercrime Intelligence
            </p>

            <div className="login-badge-row" aria-hidden="true">
              <span className="login-badge">
                <span className="login-badge-dot" />
                LAW ENFORCEMENT ACCESS
              </span>
              <span className="login-badge" style={{ background: "rgba(16,185,129,0.15)", borderColor: "rgba(16,185,129,0.3)", color: "#6ee7b7" }}>
                MHA CLASSIFIED
              </span>
            </div>
          </div>

          {/* ── FORM BODY ──────────────────────────────────── */}
          <div className="login-body">

            {/* Session expired banner */}
            {sessionExpired && !error && !success && (
              <div className="login-expired-banner" role="alert">
                <span aria-hidden="true">⚠️</span>
                Session expired. Please sign in again to continue.
              </div>
            )}

            {/* Error message */}
            {error && (
              <div className="login-error" role="alert" aria-live="assertive">
                <span className="login-error-icon"><AlertIcon /></span>
                <span>{error}</span>
              </div>
            )}

            {/* Success message */}
            {success && (
              <div className="login-success" role="status" aria-live="polite">
                <CheckIcon />
                <span>Authentication successful. Loading dashboard…</span>
              </div>
            )}

            <div className="login-section-label">Secure Sign In</div>

            <form onSubmit={handleSubmit} noValidate>
              {/* Username field */}
              <div className="login-field">
                <label className="login-label" htmlFor="drishti-username">
                  Username or Email
                </label>
                <div className="login-input-wrapper">
                  <input
                    id="drishti-username"
                    ref={usernameRef}
                    type="text"
                    className="login-input"
                    placeholder="Enter username"
                    value={username}
                    onChange={e => { setUsername(e.target.value); setError(null); }}
                    onKeyDown={handleKeyDown}
                    disabled={loading || success}
                    autoComplete="username"
                    autoCapitalize="none"
                    spellCheck={false}
                    aria-required="true"
                    aria-invalid={!!error}
                    aria-describedby={error ? "login-error-msg" : undefined}
                  />
                </div>
              </div>

              {/* Password field */}
              <div className="login-field">
                <label className="login-label" htmlFor="drishti-password">
                  Password
                </label>
                <div className="login-input-wrapper">
                  <input
                    id="drishti-password"
                    type={showPw ? "text" : "password"}
                    className="login-input login-input--password"
                    placeholder="Enter password"
                    value={password}
                    onChange={e => { setPassword(e.target.value); setError(null); }}
                    onKeyDown={handleKeyDown}
                    disabled={loading || success}
                    autoComplete="current-password"
                    aria-required="true"
                    aria-invalid={!!error}
                  />
                  <button
                    type="button"
                    className="login-pw-toggle"
                    onClick={() => setShowPw(v => !v)}
                    aria-label={showPw ? "Hide password" : "Show password"}
                    tabIndex={0}
                    disabled={loading || success}
                  >
                    {showPw ? <EyeOffIcon /> : <EyeIcon />}
                  </button>
                </div>
              </div>

              {/* Remember me */}
              <div className="login-remember-row">
                <input
                  id="drishti-remember"
                  type="checkbox"
                  className="login-checkbox"
                  checked={remember}
                  onChange={e => setRemember(e.target.checked)}
                  disabled={loading || success}
                />
                <label htmlFor="drishti-remember" className="login-remember-label">
                  Remember me on this device
                </label>
              </div>

              {/* Submit button */}
              <button
                type="submit"
                className="login-btn"
                disabled={loading || success}
                aria-busy={loading}
              >
                {loading ? (
                  <>
                    <span className="login-spinner" aria-hidden="true" />
                    Authenticating…
                  </>
                ) : success ? (
                  <>
                    <CheckIcon />
                    Authenticated
                  </>
                ) : (
                  "SIGN IN"
                )}
              </button>
            </form>

            {/* Forgot password */}
            <div className="login-footer">
              <button
                type="button"
                className="login-forgot-btn"
                onClick={() => setShowForgot(true)}
              >
                Forgot password?
              </button>
            </div>
          </div>

          {/* Bottom stripe */}
          <div className="login-card-stripe" aria-hidden="true" />
        </div>

        {/* Backend status indicator */}
        <div className="login-status-row" aria-label="System status" role="status">
          <span>
            <span
              className={`login-status-dot login-status-dot--${apiStatus}`}
              aria-hidden="true"
            />
            5D Engine {apiStatus === "ok" ? "Online" : apiStatus === "error" ? "Offline" : "Checking…"}
          </span>
          <span style={{ color: "var(--border-light)" }}>·</span>
          <span>MHA Cyber Operations</span>
          <span style={{ color: "var(--border-light)" }}>·</span>
          <span>TLS Encrypted</span>
        </div>
      </div>

      {/* Forgot Password Modal */}
      {showForgot && <ForgotPasswordModal onClose={() => setShowForgot(false)} />}
    </>
  );
}
