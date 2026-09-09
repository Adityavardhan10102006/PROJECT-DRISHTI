/**
 * src/App.jsx — Project DRISHTI Dashboard
 * Upgraded 5D Cybercrime Intelligence & Interception Platform.
 *
 * SIH26184 — Ministry of Home Affairs | Blockchain & Cybersecurity
 *
 * Authentication: JWT-gated. LoginPage is shown when unauthenticated.
 * Session expiry events trigger automatic redirect back to login.
 */

import { useState, useEffect, useCallback } from "react";
import "./App.css";
import { submitComplaint, fetchHealth, fetchFeedbackStats, fetchSimStatus, startSimulation, stopSimulation, logout } from "./api";
import { isAuthenticated, getUser, clearToken } from "./auth";
import HotspotMap         from "./components/HotspotMap";
import AlertCard          from "./components/AlertCard";
import ComplaintForm      from "./components/ComplaintForm";
import FiveDDetailPanel   from "./components/FiveDDetailPanel";
import AboutModal         from "./components/AboutModal";
import OutcomeModal       from "./components/OutcomeModal";
import ModelMetricsModal  from "./components/ModelMetricsModal";
import CommandCenterView  from "./components/CommandCenterView";
import CasesListView      from "./components/CasesListView";
import CaseDetailView     from "./components/CaseDetailView";
import TimelineView       from "./components/TimelineView";
import MoneyTrailView     from "./components/MoneyTrailView";
import ModelIntelligenceView from "./components/ModelIntelligenceView";
import AuditLogView       from "./components/AuditLogView";
import SystemStatusView   from "./components/SystemStatusView";
import LoginPage          from "./LoginPage";

function EyeIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
      stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
      <circle cx="12" cy="12" r="3"/>
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
      <polyline points="16 17 21 12 16 7"/>
      <line x1="21" y1="12" x2="9" y2="12"/>
    </svg>
  );
}

function UserBadge({ user, onLogout, loggingOut }) {
  const roleColors = {
    admin:       { bg: "rgba(124, 58, 237, 0.2)",  border: "#7c3aed", color: "#c4b5fd" },
    analyst:     { bg: "rgba(59, 130, 246, 0.2)",  border: "#3b82f6", color: "#93c5fd" },
    investigator:{ bg: "rgba(16, 185, 129, 0.15)", border: "#10b981", color: "#6ee7b7" },
  };
  const rc = roleColors[user?.role] || roleColors.analyst;

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      {/* User info pill */}
      <div style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-end",
        lineHeight: 1.2,
      }}>
        <span style={{ fontSize: 11, fontWeight: 600, color: "var(--text-primary)" }}>
          {user?.username?.toUpperCase() || "USER"}
        </span>
        <span style={{
          fontSize: 9,
          fontWeight: 700,
          letterSpacing: "1px",
          color: rc.color,
          background: rc.bg,
          border: `1px solid ${rc.border}`,
          borderRadius: "3px",
          padding: "1px 5px",
          marginTop: 1,
        }}>
          {(user?.role || "analyst").toUpperCase()}
        </span>
      </div>

      {/* Logout button */}
      <button
        type="button"
        className="topnav-about-btn"
        onClick={onLogout}
        disabled={loggingOut}
        title="Sign out of DRISHTI"
        style={{
          display: "flex",
          alignItems: "center",
          gap: 5,
          color: loggingOut ? "var(--text-muted)" : "var(--text-secondary)",
        }}
        aria-label="Sign out"
      >
        <LogoutIcon />
        {loggingOut ? "Signing out…" : "Logout"}
      </button>
    </div>
  );
}

export default function App() {
  // ── Auth State ───────────────────────────────────────────────
  const [authed,         setAuthed]         = useState(() => isAuthenticated());
  const [currentUser,    setCurrentUser]    = useState(() => authed ? getUser() : null);
  const [sessionExpired, setSessionExpired] = useState(false);
  const [loggingOut,     setLoggingOut]     = useState(false);

  // ── Dashboard State ─────────────────────────────────────────
  const [predictions,    setPredictions]    = useState([]);
  const [loading,        setLoading]        = useState(false);
  const [error,          setError]          = useState(null);
  const [focused,        setFocused]        = useState(null);
  const [activeTarget,   setActiveTarget]   = useState(null);
  const [apiStatus,      setApiStatus]      = useState(null);
  const [newId,          setNewId]          = useState(null);
  const [feedbackStats,  setFeedbackStats]  = useState(null);
  const [rightView,      setRightView]      = useState("queue");
  const [showAbout,      setShowAbout]      = useState(false);
  const [showMetrics,    setShowMetrics]    = useState(false);
  const [outcomeTarget,  setOutcomeTarget]  = useState(null);
  const [simActive,      setSimActive]      = useState(false);
  const [simEvents,      setSimEvents]      = useState(0);
  const [activeTab,      setActiveTab]      = useState("command_center");
  const [selectedCaseId, setSelectedCaseId] = useState("DR-2026-1001");

  const handleSelectCase = (caseId) => {
    setSelectedCaseId(caseId);
    setActiveTab("case_detail");
  };

  // ── Session Expiry Listener ─────────────────────────────────
  useEffect(() => {
    function onSessionExpired() {
      clearToken();
      setAuthed(false);
      setCurrentUser(null);
      setSessionExpired(true);
      setPredictions([]);
      setFocused(null);
    }
    window.addEventListener("drishti:session-expired", onSessionExpired);
    return () => window.removeEventListener("drishti:session-expired", onSessionExpired);
  }, []);

  // ── After Login ──────────────────────────────────────────────
  function handleLogin(userInfo) {
    setCurrentUser(userInfo || getUser());
    setSessionExpired(false);
    setAuthed(true);
  }

  // ── Logout ───────────────────────────────────────────────────
  async function handleLogout() {
    setLoggingOut(true);
    try {
      await logout();
    } finally {
      setPredictions([]);
      setFocused(null);
      setCurrentUser(null);
      setAuthed(false);
      setLoggingOut(false);
      setSessionExpired(false);
    }
  }

  // ── Load Health & Feedback Stats on Mount ───────────────────
  useEffect(() => {
    if (!authed) return;
    fetchHealth()
      .then(h => setApiStatus(h))
      .catch(() => setApiStatus({ status: "error" }));
    loadStats();
    checkSimStatus();
  }, [authed]);

  function checkSimStatus() {
    fetchSimStatus()
      .then(s => {
        setSimActive(!!s.is_running);
        setSimEvents(s.total_streamed || 0);
      })
      .catch(() => {});
  }

  async function handleToggleSimulation() {
    try {
      if (simActive) {
        await stopSimulation();
        setSimActive(false);
      } else {
        await startSimulation(2.0);
        setSimActive(true);
      }
      checkSimStatus();
    } catch (e) {
      console.warn("Simulation toggle error:", e);
    }
  }

  function loadStats() {
    fetchFeedbackStats()
      .then(s => setFeedbackStats(s))
      .catch(err => console.warn("Feedback stats not loaded yet:", err));
  }

  // ── Submit Complaint ────────────────────────────────────────
  async function handleSubmit(payload) {
    setLoading(true);
    setError(null);
    try {
      const result = await submitComplaint(payload);
      setPredictions(prev => [result, ...prev]);
      setFocused(result);
      setActiveTarget(result.top_k_locations?.[0] || result.hotspot);
      setNewId(result.complaint_id);
      setRightView("dossier");
      setTimeout(() => setNewId(null), 800);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // ── Select Alert from List ──────────────────────────────────
  function handleSelectAlert(pred) {
    setFocused(pred);
    setActiveTarget(pred.top_k_locations?.[0] || pred.hotspot);
  }

  function handleInspectAlert(pred) {
    setFocused(pred);
    setActiveTarget(pred.top_k_locations?.[0] || pred.hotspot);
    setRightView("dossier");
  }

  function handleSelectCandidate(cand) {
    setActiveTarget(cand);
  }

  // ── Map Center Coordinate ────────────────────────────────────
  const primaryCandidate = focused?.top_k_locations?.[0] || focused?.hotspot;
  const mapCenter = activeTarget?.lat && activeTarget?.lon
    ? [activeTarget.lat, activeTarget.lon]
    : primaryCandidate
    ? [primaryCandidate.lat, primaryCandidate.lon]
    : [20.5937, 78.9629];

  const apiOnline = apiStatus?.status === "ok";

  // ── RENDER: Login Gate ───────────────────────────────────────
  if (!authed) {
    return (
      <LoginPage
        onLogin={handleLogin}
        sessionExpired={sessionExpired}
      />
    );
  }

  // ── RENDER: Full Dashboard ───────────────────────────────────
  return (
    <div className="app">
      {/* ── TOP NAV ─────────────────────────────────────── */}
      <nav className="topnav">
        <div className="topnav-brand">
          <EyeIcon />
          <span className="topnav-logo">DRISHTI</span>
          <span className="topnav-subtitle">
            5D Cybercrime Intelligence &amp; Interception
          </span>
          <span className="sih-badge">SIH 2026 · SIH26184</span>
        </div>

        {/* Dynamic Metric Badges */}
        {feedbackStats && feedbackStats.total_validations > 0 && (
          <div className="top-metrics-strip">
            <div className="metric-tag">
              <span className="metric-num">{feedbackStats.total_validations}</span>
              <span className="metric-lbl">Audited Cases</span>
            </div>
            <div className="metric-tag">
              <span className="metric-num text-green">
                {Math.round(feedbackStats.interception_success_rate * 100)}%
              </span>
              <span className="metric-lbl">Interceptions</span>
            </div>
            <div className="metric-tag">
              <span className="metric-num text-yellow">
                Rs {Math.round(feedbackStats.total_recovered_amount).toLocaleString("en-IN")}
              </span>
              <span className="metric-lbl">Total Recovered</span>
            </div>
          </div>
        )}

        <div className="topnav-status">
          {/* Real-Time Simulation Stream Toggle */}
          <button
            type="button"
            className="topnav-about-btn"
            style={{
              background: simActive ? "rgba(239, 68, 68, 0.2)" : "rgba(30, 41, 59, 0.7)",
              borderColor: simActive ? "#ef4444" : "var(--border-light)",
              color: simActive ? "#f87171" : "var(--text-secondary)",
            }}
            onClick={handleToggleSimulation}
            title="Stream synthetic live transactions (DEMO / SIMULATION MODE)"
          >
            {simActive ? `🔴 SIM STREAM ACTIVE (${simEvents})` : "▶ START SIMULATION"}
          </button>

          {/* Model Metrics Modal Toggle */}
          <button
            type="button"
            className="topnav-about-btn"
            onClick={() => setShowMetrics(true)}
            title="Inspect Model Evaluation Metrics"
          >
            📊 ML Metrics
          </button>

          {/* About / Context Button */}
          <button
            type="button"
            className="topnav-about-btn"
            onClick={() => setShowAbout(true)}
            title="View SIH 2026 Problem Statement & 5D Architecture"
          >
            ℹ️ About DRISHTI
          </button>

          <span>
            <span
              className="status-dot"
              style={{ background: apiOnline ? "var(--alert-low)" : "var(--alert-critical)" }}
            />
            5D Engine {apiOnline ? "Active" : "Offline"}
          </span>
          <span style={{ color: "var(--border-light)" }}>|</span>
          <span style={{ color: "#38bdf8", fontSize: "11px", fontWeight: 600 }}>
            MHA Cyber Operations
          </span>

          {/* ── User Info + Logout ── */}
          <span style={{ color: "var(--border-light)" }}>|</span>
          <UserBadge
            user={currentUser}
            onLogout={handleLogout}
            loggingOut={loggingOut}
          />
        </div>
      </nav>

      {/* ── PRIMARY INTELLIGENCE NAVIGATION BAR ──────────── */}
      <div className="platform-nav-strip">
        <button
          className={`nav-tab-btn ${activeTab === "command_center" ? "active" : ""}`}
          onClick={() => setActiveTab("command_center")}
        >
          📊 COMMAND CENTER
        </button>
        <button
          className={`nav-tab-btn ${activeTab === "cases" || activeTab === "case_detail" ? "active" : ""}`}
          onClick={() => setActiveTab("cases")}
        >
          📁 CASES
        </button>
        <button
          className={`nav-tab-btn ${activeTab === "analyze" ? "active" : ""}`}
          onClick={() => setActiveTab("analyze")}
        >
          🔍 ANALYZE COMPLAINT
        </button>
        <button
          className={`nav-tab-btn ${activeTab === "trail" ? "active" : ""}`}
          onClick={() => setActiveTab("trail")}
        >
          🕸️ MONEY TRAIL
        </button>
        <button
          className={`nav-tab-btn ${activeTab === "map" ? "active" : ""}`}
          onClick={() => setActiveTab("map")}
        >
          🗺️ MAP INTELLIGENCE
        </button>
        <button
          className={`nav-tab-btn ${activeTab === "models" ? "active" : ""}`}
          onClick={() => setActiveTab("models")}
        >
          ⚡ MODEL INTELLIGENCE
        </button>
        {(currentUser?.role === "admin" || currentUser?.role === "analyst") && (
          <button
            className={`nav-tab-btn ${activeTab === "audit" ? "active" : ""}`}
            onClick={() => setActiveTab("audit")}
          >
            📋 AUDIT LOG
          </button>
        )}
        <button
          className={`nav-tab-btn ${activeTab === "status" ? "active" : ""}`}
          onClick={() => setActiveTab("status")}
        >
          🛡️ SYSTEM STATUS
        </button>
      </div>

      {/* ── VIEW ROUTING ─────────────────────────────────── */}
      {activeTab === "command_center" && (
        <CommandCenterView
          onSelectCase={handleSelectCase}
          onNavigate={(tab) => setActiveTab(tab)}
        />
      )}

      {activeTab === "cases" && (
        <CasesListView onSelectCase={handleSelectCase} />
      )}

      {activeTab === "case_detail" && (
        <CaseDetailView
          caseId={selectedCaseId}
          onBack={() => setActiveTab("cases")}
        />
      )}

      {activeTab === "trail" && (
        <MoneyTrailView selectedCaseId={selectedCaseId} />
      )}

      {activeTab === "map" && (
        <div className="fullpage-map-container">
          <HotspotMap
            prediction={focused}
            predictions={predictions}
            activeTarget={activeTarget}
            center={mapCenter}
            onSelectCandidate={handleSelectCandidate}
          />
        </div>
      )}

      {activeTab === "models" && (
        <ModelIntelligenceView />
      )}

      {activeTab === "audit" && (
        <AuditLogView />
      )}

      {activeTab === "status" && (
        <SystemStatusView />
      )}

      {/* ── TAB: ANALYZE COMPLAINT (Original 3-Column Dashboard) ── */}
      {activeTab === "analyze" && (
        <div className="dashboard">
          {/* LEFT: Complaint form */}
          <ComplaintForm
            onSubmit={handleSubmit}
            loading={loading}
            error={error}
          />

          {/* CENTER: Map */}
          <div className="map-panel">
            <HotspotMap
              prediction={focused}
              predictions={predictions}
              activeTarget={activeTarget}
              center={mapCenter}
              onSelectCandidate={handleSelectCandidate}
            />
            <div className="map-overlay">
              Leaflet GIS · Multi-Cluster DBSCAN &amp; Tactical Dispatch · {predictions.length} case{predictions.length !== 1 ? "s" : ""}
            </div>
            <div className="map-radar">
              {focused ? `ACTIVE TARGET: ${focused.complaint_id}` : "AWAITING COMPLAINT"}
            </div>
          </div>

          {/* RIGHT: Alert Queue / 5D Dossier View */}
          <div className="right-panel">
            <div className="alerts-header">
              <div className="right-tab-group">
                <button
                  type="button"
                  className={`right-tab-btn ${rightView === "queue" ? "active" : ""}`}
                  onClick={() => setRightView("queue")}
                >
                  📋 Priority Queue
                  {predictions.length > 0 && (
                    <span className="tab-counter">{predictions.length}</span>
                  )}
                </button>

                <button
                  type="button"
                  className={`right-tab-btn ${rightView === "dossier" ? "active" : ""}`}
                  onClick={() => setRightView("dossier")}
                  disabled={!focused}
                >
                  🔍 5D Dossier
                  {focused && <span className="tab-active-dot"></span>}
                </button>
              </div>
            </div>

            {rightView === "queue" && (
              <div className="alerts-list">
                {predictions.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">🛡️</div>
                    <div className="empty-title">5D Intelligence Ready</div>
                    <div className="empty-desc">
                      Submit a cybercrime complaint from the left panel (or click a <strong>Quick Load Demo</strong> preset) to forecast cash-out locations, trace mule networks, and compute patrol unit dispatch ETAs.
                    </div>
                  </div>
                ) : (
                  predictions.map(p => (
                    <AlertCard
                      key={p.complaint_id}
                      prediction={p}
                      isSelected={focused?.complaint_id === p.complaint_id}
                      isNew={p.complaint_id === newId}
                      onClick={handleSelectAlert}
                      onInspect={handleInspectAlert}
                      onFeedbackLogged={loadStats}
                    />
                  ))
                )}
              </div>
            )}

            {rightView === "dossier" && (
              <FiveDDetailPanel
                prediction={focused}
                onOpenOutcomeModal={() => setOutcomeTarget(focused)}
                onSelectLocation={handleSelectCandidate}
                onBackToList={() => setRightView("queue")}
              />
            )}
          </div>
        </div>
      )}

      {/* ── Modals ── */}
      {showAbout && (
        <AboutModal onClose={() => setShowAbout(false)} />
      )}

      {outcomeTarget && (
        <OutcomeModal
          prediction={outcomeTarget}
          onClose={() => setOutcomeTarget(null)}
          onFeedbackSubmitted={() => {
            loadStats();
          }}
        />
      )}

      {showMetrics && (
        <ModelMetricsModal
          metrics={apiStatus?.model_metrics}
          onClose={() => setShowMetrics(false)}
        />
      )}
    </div>
  );
}
