/**
 * src/App.jsx — Project DRISHTI Dashboard
 * Upgraded 5D Cybercrime Intelligence & Interception Platform.
 *
 * SIH26184 — Ministry of Home Affairs | Blockchain & Cybersecurity
 */

import { useState, useEffect } from "react";
import "./App.css";
import { submitComplaint, fetchHealth, fetchFeedbackStats } from "./api";
import HotspotMap         from "./components/HotspotMap";
import AlertCard          from "./components/AlertCard";
import ComplaintForm      from "./components/ComplaintForm";
import FiveDDetailPanel   from "./components/FiveDDetailPanel";
import AboutModal         from "./components/AboutModal";
import OutcomeModal       from "./components/OutcomeModal";

function EyeIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
      stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
      <circle cx="12" cy="12" r="3"/>
    </svg>
  );
}

export default function App() {
  const [predictions,    setPredictions]    = useState([]);
  const [loading,        setLoading]        = useState(false);
  const [error,          setError]          = useState(null);
  const [focused,        setFocused]        = useState(null);
  const [activeTarget,   setActiveTarget]   = useState(null);
  const [apiStatus,      setApiStatus]      = useState(null);
  const [newId,          setNewId]          = useState(null);
  const [feedbackStats,  setFeedbackStats]  = useState(null);
  const [rightView,      setRightView]      = useState("queue"); // "queue" | "dossier"
  const [showAbout,      setShowAbout]      = useState(false);
  const [outcomeTarget,  setOutcomeTarget]  = useState(null);

  // ── Load Health & Feedback Stats on Mount ───────────────────
  useEffect(() => {
    fetchHealth()
      .then(h => setApiStatus(h))
      .catch(() => setApiStatus({ status: "error" }));

    loadStats();
  }, []);

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
      setRightView("dossier"); // Auto-switch to full 5D Dossier on prediction
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
        </div>
      </nav>

      {/* ── THREE-COLUMN DASHBOARD ───────────────────────── */}
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
          {/* View Mode Switcher Header */}
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

          {/* Tab 1: Ranked Alert Queue */}
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

          {/* Tab 2: Full 5D Intelligence Dossier */}
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
    </div>
  );
}
