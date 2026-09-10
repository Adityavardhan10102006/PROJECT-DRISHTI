/**
 * src/App.jsx — Project DRISHTI Dashboard
 * Upgraded 5D Cybercrime Intelligence & Tactical Command Center.
 *
 * SIH26184 — Ministry of Home Affairs | Blockchain & Cybersecurity
 *
 * Authentication: JWT-gated. LoginPage is shown when unauthenticated.
 * Session expiry events trigger automatic redirect back to login.
 */

import { useState, useEffect, useCallback } from "react";
import "./App.css";
import {
  submitComplaint,
  fetchHealth,
  fetchFeedbackStats,
  fetchSimStatus,
  startSimulation,
  stopSimulation,
  logout,
} from "./api";
import { isAuthenticated, getUser, clearToken } from "./auth";

// Core Components
import HotspotMap from "./components/HotspotMap";
import AboutModal from "./components/AboutModal";
import OutcomeModal from "./components/OutcomeModal";
import ModelMetricsModal from "./components/ModelMetricsModal";
import CommandCenterView from "./components/CommandCenterView";
import CasesListView from "./components/CasesListView";
import CaseDetailView from "./components/CaseDetailView";
import MoneyTrailView from "./components/MoneyTrailView";
import ModelIntelligenceView from "./components/ModelIntelligenceView";
import AuditLogView from "./components/AuditLogView";
import SystemStatusView from "./components/SystemStatusView";
import SidebarNav from "./components/SidebarNav";
import AlertsCenterView from "./components/AlertsCenterView";
import PredictionView from "./components/PredictionView";
import FieldOperationsView from "./components/FieldOperationsView";
import BackendOfflineBanner from "./components/BackendOfflineBanner";
import LoginPage from "./LoginPage";

function EyeIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
      stroke="var(--accent)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
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
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      {/* User info pill */}
      <div style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-end",
        lineHeight: 1.1,
      }}>
        <span style={{ fontSize: 11, fontWeight: 700, color: "var(--text-primary)" }}>
          {user?.username?.toUpperCase() || "USER"}
        </span>
        <span style={{
          fontSize: 9,
          fontWeight: 800,
          letterSpacing: "1px",
          color: rc.color,
          background: rc.bg,
          border: `1px solid ${rc.border}`,
          borderRadius: "3px",
          padding: "1px 5px",
          marginTop: 2,
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

  // ── Layout & View State ──────────────────────────────────────
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeTab,        setActiveTab]        = useState("command_center");
  const [selectedCaseId,   setSelectedCaseId]   = useState("DR-2026-1001");

  // ── Telemetry & Modal State ──────────────────────────────────
  const [predictions,    setPredictions]    = useState([]);
  const [focused,        setFocused]        = useState(null);
  const [activeTarget,   setActiveTarget]   = useState(null);
  const [apiStatus,      setApiStatus]      = useState(null);
  const [feedbackStats,  setFeedbackStats]  = useState(null);
  const [showAbout,      setShowAbout]      = useState(false);
  const [showMetrics,    setShowMetrics]    = useState(false);
  const [outcomeTarget,  setOutcomeTarget]  = useState(null);
  const [simActive,      setSimActive]      = useState(false);
  const [simEvents,      setSimEvents]      = useState(0);

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

  function handleSelectCandidate(cand) {
    setActiveTarget(cand);
  }

  // ── Map Center Coordinate ────────────────────────────────────
  const primaryCandidate = focused?.top_k_locations?.[0] || focused?.hotspot;
  const mapCenter = activeTarget?.lat && activeTarget?.lon
    ? [activeTarget.lat, activeTarget.lon]
    : primaryCandidate
    ? [primaryCandidate.lat, primaryCandidate.lon]
    : [17.4435, 78.3772];

  const apiOnline = apiStatus?.status === "healthy" || apiStatus?.status === "ok";

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
      {/* Backend Offline Banner */}
      <BackendOfflineBanner />

      {/* ── TOP NAV ─────────────────────────────────────── */}
      <nav className="topnav">
        <div className="topnav-brand">
          <EyeIcon />
          <span className="topnav-logo">DRISHTI</span>
          <span className="topnav-subtitle">
            Tactical Cybercrime SOC
          </span>
          <span className="sih-badge">SIH26184</span>
        </div>

        {/* Dynamic Metric Badges */}
        {feedbackStats && feedbackStats.total_validations > 0 && (
          <div className="top-metrics-strip">
            <div className="metric-tag">
              <span className="metric-num">{feedbackStats.total_validations}</span>
              <span className="metric-lbl">Audited</span>
            </div>
            <div className="metric-tag">
              <span className="metric-num text-green">
                {Math.round(feedbackStats.interception_success_rate * 100)}%
              </span>
              <span className="metric-lbl">Interceptions</span>
            </div>
            <div className="metric-tag">
              <span className="metric-num text-yellow">
                ₹{Math.round(feedbackStats.total_recovered_amount).toLocaleString("en-IN")}
              </span>
              <span className="metric-lbl">Recovered</span>
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
            {simActive ? `🔴 SIM ACTIVE (${simEvents})` : "▶ STREAM SIMULATION"}
          </button>

          {/* Model Metrics Modal Toggle */}
          <button
            type="button"
            className="topnav-about-btn"
            onClick={() => setShowMetrics(true)}
            title="Inspect Model Evaluation Metrics"
          >
            📊 ML Benchmarks
          </button>

          {/* About / Context Button */}
          <button
            type="button"
            className="topnav-about-btn"
            onClick={() => setShowAbout(true)}
            title="View SIH 2026 Problem Statement & 5D Architecture"
          >
            ℹ️ About
          </button>

          <span>
            <span
              className="status-dot"
              style={{ background: apiOnline ? "var(--alert-low)" : "var(--alert-critical)" }}
            />
            {apiOnline ? "Engine Ready" : "Engine Offline"}
          </span>

          <span style={{ color: "var(--border-light)" }}>|</span>

          {/* User Info + Logout */}
          <UserBadge
            user={currentUser}
            onLogout={handleLogout}
            loggingOut={loggingOut}
          />
        </div>
      </nav>

      {/* ── APP WORKSPACE: SIDEBAR + ACTIVE VIEW ─────────── */}
      <div className="app-main-layout">
        {/* Collapsible Persistent Navigation Sidebar */}
        <SidebarNav
          activeTab={activeTab}
          onNavigate={(tab) => {
            if (tab === "about") {
              setShowAbout(true);
            } else {
              setActiveTab(tab);
            }
          }}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          activeAlertCount={predictions.length > 0 ? predictions.length : 2}
          activeCaseCount={5}
          userRole={currentUser?.role || "analyst"}
        />

        {/* Dynamic Viewport Container */}
        <main className="app-view-container">
          {activeTab === "command_center" && (
            <CommandCenterView
              onSelectCase={handleSelectCase}
              onNavigate={(tab) => setActiveTab(tab)}
              focusedPrediction={focused}
              predictions={predictions}
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

          {activeTab === "prediction" && (
            <PredictionView
              onSelectCase={handleSelectCase}
              onPredictionComplete={(res) => {
                setPredictions((prev) => [res, ...prev]);
                setFocused(res);
                setActiveTarget(res.top_k_locations?.[0] || res.hotspot);
              }}
            />
          )}

          {activeTab === "trail" && (
            <MoneyTrailView selectedCaseId={selectedCaseId} />
          )}

          {activeTab === "map" && (
            <div className="fullpage-map-container" style={{ height: "calc(100vh - 52px)", position: "relative" }}>
              <HotspotMap
                prediction={focused}
                predictions={predictions}
                activeTarget={activeTarget}
                center={mapCenter}
                onSelectCandidate={handleSelectCandidate}
              />
            </div>
          )}

          {activeTab === "alerts" && (
            <AlertsCenterView
              onSelectCase={handleSelectCase}
              onNavigate={(tab) => setActiveTab(tab)}
            />
          )}

          {activeTab === "operations" && (
            <FieldOperationsView onSelectCase={handleSelectCase} />
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
        </main>
      </div>

      {/* ── MODALS ───────────────────────────────────────── */}
      {showAbout && <AboutModal onClose={() => setShowAbout(false)} />}
      {showMetrics && <ModelMetricsModal onClose={() => setShowMetrics(false)} />}
      {outcomeTarget && (
        <OutcomeModal
          target={outcomeTarget}
          onClose={() => setOutcomeTarget(null)}
          onSuccess={loadStats}
        />
      )}
    </div>
  );
}
