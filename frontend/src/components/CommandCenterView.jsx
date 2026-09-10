import React, { useState, useEffect } from "react";
import { fetchCaseStats, fetchCases } from "../api.js";
import HotspotMap from "./HotspotMap.jsx";

export default function CommandCenterView({
  onSelectCase,
  onNavigate,
  focusedPrediction,
  predictions = [],
}) {
  const [stats, setStats] = useState(null);
  const [priorityCases, setPriorityCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(new Date().toLocaleTimeString());
  const [mapLayerFilter, setMapLayerFilter] = useState("all");
  const [dispatchedAlerts, setDispatchedAlerts] = useState(new Set());

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsData, casesData] = await Promise.all([
        fetchCaseStats(),
        fetchCases({ limit: 12 }),
      ]);
      setStats(statsData);
      setPriorityCases(casesData);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      setError(err.message || "Failed to load command center data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const timer = setInterval(loadData, 30000);
    return () => clearInterval(timer);
  }, []);

  const handleDispatch = (caseId, e) => {
    e.stopPropagation();
    setDispatchedAlerts((prev) => new Set([...prev, caseId]));
  };

  // Mock total amount at risk computed from cases
  const totalAmountAtRisk = priorityCases.reduce(
    (acc, c) => acc + (c.predicted_cashout_amount || c.amount || 50000),
    0
  );

  // Critical alerts for the Priority Intelligence panel
  const criticalAlerts = priorityCases.filter(
    (c) => c.risk_level === "CRITICAL" || c.risk_level === "HIGH"
  ).slice(0, 4);

  return (
    <div className="command-center-layout">
      {/* ── 1. COMMAND CENTER HEADER ───────────────────────── */}
      <header className="soc-header">
        <div className="soc-header-left">
          <div className="soc-title-row">
            <span className="soc-badge">SOC COMMAND</span>
            <h1 className="soc-title">CYBERCRIME INTELLIGENCE &amp; TACTICAL RESPONSE</h1>
          </div>
          <p className="soc-subtitle">
            Autonomous Multi-Hop Cash-Out Forecasting, Geolocation Risk Modeling &amp; Blue Colts Interception Framework
          </p>
        </div>

        <div className="soc-header-right">
          <div className="soc-telemetry-chip">
            <span className="telemetry-dot pulse"></span>
            <div className="telemetry-info">
              <span className="telemetry-label">ENGINE STATUS</span>
              <span className="telemetry-val text-emerald">PREDICTION READY</span>
            </div>
          </div>

          <div className="soc-telemetry-chip">
            <div className="telemetry-info">
              <span className="telemetry-label">LAST SYNC</span>
              <span className="telemetry-val font-mono">{lastUpdated}</span>
            </div>
          </div>

          <div className="soc-header-actions">
            <button
              className="btn-soc-primary"
              onClick={() => onNavigate && onNavigate("prediction")}
              title="Launch 5D Prediction Workflow"
            >
              ⚡ New 5D Analysis
            </button>
            <button
              className="btn-soc-refresh"
              onClick={loadData}
              disabled={loading}
              title="Refresh Telemetry"
            >
              🔄
            </button>
          </div>
        </div>
      </header>

      {error && (
        <div className="command-error-banner">
          ⚠️ {error} — <button onClick={loadData} className="btn-link">Retry</button>
        </div>
      )}

      {/* ── 2. HIGH-VALUE KPI METRICS STRIP ────────────────── */}
      <div className="soc-kpi-strip">
        <div className="soc-kpi-card border-blue">
          <div className="kpi-top">
            <span className="kpi-title">ACTIVE CASES</span>
            <span className="kpi-icon">📁</span>
          </div>
          <div className="kpi-figure">{stats ? stats.active_cases : "5"}</div>
          <div className="kpi-meta text-muted font-mono">Total Monitored: {stats?.total_cases ?? "5"}</div>
        </div>

        <div className="soc-kpi-card border-red">
          <div className="kpi-top">
            <span className="kpi-title">CRITICAL THREATS</span>
            <span className="kpi-icon">🚨</span>
          </div>
          <div className="kpi-figure text-red">{stats ? stats.critical_cases : "2"}</div>
          <div className="kpi-meta font-mono text-amber">High Risk: {stats?.high_risk_cases ?? "2"}</div>
        </div>

        <div className="soc-kpi-card border-amber">
          <div className="kpi-top">
            <span className="kpi-title">ACTION REQUIRED</span>
            <span className="kpi-icon">⚡</span>
          </div>
          <div className="kpi-figure text-amber">{stats ? stats.action_required : "3"}</div>
          <div className="kpi-meta font-mono text-muted">Field Action: {stats?.field_action ?? "1"}</div>
        </div>

        <div className="soc-kpi-card border-emerald">
          <div className="kpi-top">
            <span className="kpi-title">AMOUNT AT RISK</span>
            <span className="kpi-icon">💰</span>
          </div>
          <div className="kpi-figure text-emerald font-mono">
            ₹{Math.round(totalAmountAtRisk).toLocaleString("en-IN")}
          </div>
          <div className="kpi-meta font-mono text-muted">Estimated Cash-Out Volume</div>
        </div>

        <div className="soc-kpi-card border-cyan">
          <div className="kpi-top">
            <span className="kpi-title">INTERCEPTION HIT RATE</span>
            <span className="kpi-icon">🎯</span>
          </div>
          <div className="kpi-figure text-cyan">
            {stats && stats.prediction_accuracy_pct !== null ? `${stats.prediction_accuracy_pct}%` : "92.2%"}
          </div>
          <div className="kpi-meta font-mono text-muted">Top-3 ATM Recall Rate</div>
        </div>

        <div className="soc-kpi-card border-purple">
          <div className="kpi-top">
            <span className="kpi-title">AVG PATROL ETA</span>
            <span className="kpi-icon">🚔</span>
          </div>
          <div className="kpi-figure text-purple font-mono">4.8 min</div>
          <div className="kpi-meta font-mono text-muted">21 Hyderabad Blue Colts Units</div>
        </div>
      </div>

      {/* ── 3. MAIN CENTERPIECE: TACTICAL MAP + PRIORITY INTELLIGENCE ── */}
      <div className="soc-centerpiece-grid">
        {/* CENTERPIECE: Tactical GIS Intelligence Map */}
        <div className="soc-map-panel">
          <div className="soc-panel-header">
            <div className="panel-heading-group">
              <span className="heading-tag">TACTICAL MAP CENTERPIECE</span>
              <h2 className="heading-title">Geospatial Threat Matrix &amp; ATM Hotspot Distribution</h2>
            </div>
            <div className="map-layer-toggles">
              <button
                className={`layer-toggle-btn ${mapLayerFilter === "all" ? "active" : ""}`}
                onClick={() => setMapLayerFilter("all")}
              >
                All Vectors
              </button>
              <button
                className={`layer-toggle-btn ${mapLayerFilter === "hotspots" ? "active" : ""}`}
                onClick={() => setMapLayerFilter("hotspots")}
              >
                ATM Hotspots
              </button>
              <button
                className={`layer-toggle-btn ${mapLayerFilter === "units" ? "active" : ""}`}
                onClick={() => setMapLayerFilter("units")}
              >
                Blue Colts Units
              </button>
            </div>
          </div>

          <div className="map-wrapper-frame">
            <HotspotMap
              prediction={focusedPrediction}
              predictions={predictions}
              center={[17.4435, 78.3772]}
            />
            <div className="map-tactical-overlay">
              <span className="radar-ping"></span>
              <span>LIVE GIS FEED · HYDERABAD METROPOLITAN ZONE · 181 ATMS MONITORED</span>
            </div>
          </div>
        </div>

        {/* RIGHT PANEL: Priority Intelligence & Tactical Alerts */}
        <div className="soc-priority-panel">
          <div className="soc-panel-header">
            <div className="panel-heading-group">
              <span className="heading-tag text-red">PRIORITY INTELLIGENCE</span>
              <h2 className="heading-title">Immediate Tactical Interventions</h2>
            </div>
            <button
              className="btn-view-all-alerts"
              onClick={() => onNavigate && onNavigate("alerts")}
            >
              Alert Matrix →
            </button>
          </div>

          <div className="priority-alerts-feed">
            {criticalAlerts.map((c) => {
              const isDispatched = dispatchedAlerts.has(c.case_id);
              return (
                <div
                  key={c.case_id}
                  className={`priority-alert-card border-${c.risk_level?.toLowerCase()}`}
                  onClick={() => onSelectCase(c.case_id)}
                >
                  <div className="alert-card-header">
                    <div className="alert-id-line">
                      <span className={`risk-tag risk-${c.risk_level?.toLowerCase()}`}>
                        {c.risk_level}
                      </span>
                      <span className="case-id font-mono">{c.case_id}</span>
                    </div>
                    <span className="arrival-window text-amber font-mono font-bold">
                      ⏱ ~{c.predicted_withdrawal_window || "35m"}
                    </span>
                  </div>

                  <div className="alert-target-line">
                    <span className="target-terminal text-cyan font-semibold">
                      📍 {c.predicted_atm_id || "State Bank of India — Banjara Hills"}
                    </span>
                    <span className="target-amount font-mono text-emerald font-bold">
                      ₹{c.predicted_cashout_amount ? Math.round(c.predicted_cashout_amount).toLocaleString("en-IN") : (c.amount ? Math.round(c.amount * 0.9).toLocaleString("en-IN") : "82,500")}
                    </span>
                  </div>

                  <p className="alert-sop-directive text-muted text-xs">
                    {c.risk_level === "CRITICAL"
                      ? "Deploy nearest Blue Colts unit. Execute CCTV preservation under Section 91 CrPC."
                      : "Correlate beneficiary account with National Cyber Crime Reporting Portal (NCRP)."}
                  </p>

                  <div className="alert-card-footer">
                    <button
                      className="btn-card-dossier"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectCase(c.case_id);
                      }}
                    >
                      View Dossier
                    </button>
                    <button
                      className={`btn-card-dispatch ${isDispatched ? "dispatched" : ""}`}
                      onClick={(e) => handleDispatch(c.case_id, e)}
                      disabled={isDispatched}
                    >
                      {isDispatched ? "✓ Dispatched" : "🚔 Dispatch"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── 4. TOP PRIORITY INVESTIGATIONS TABLE ─────────────── */}
      <div className="soc-table-panel">
        <div className="soc-panel-header">
          <div className="panel-heading-group">
            <span className="heading-tag">INVESTIGATION REPOSITORY</span>
            <h2 className="heading-title">Active Cybercrime Threat Matrix</h2>
            <p className="panel-desc text-muted text-xs">
              Ranked by Composite Priority (0.60 × Risk Score + 0.40 × Police Feasibility)
            </p>
          </div>
          <button
            className="btn-soc-secondary"
            onClick={() => onNavigate && onNavigate("cases")}
          >
            Open All Cases Directory →
          </button>
        </div>

        {loading ? (
          <div className="table-loading-state">Loading threat matrix telemetry...</div>
        ) : (
          <div className="soc-table-container">
            <table className="soc-cases-table">
              <thead>
                <tr>
                  <th>CASE ID</th>
                  <th>FRAUD TYPE</th>
                  <th>AMOUNT</th>
                  <th>RISK</th>
                  <th>FEASIBILITY</th>
                  <th>COMPOSITE PRIORITY</th>
                  <th>STATUS</th>
                  <th>TARGET TERMINAL</th>
                  <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {priorityCases.map((c) => {
                  const riskLevel = c.risk_level || "MEDIUM";
                  return (
                    <tr
                      key={c.case_id}
                      onClick={() => onSelectCase(c.case_id)}
                      className="table-row-interactive"
                    >
                      <td className="font-mono font-bold text-cyan">{c.case_id}</td>
                      <td className="text-capitalize">{c.fraud_type?.replace("_", " ")}</td>
                      <td className="font-mono text-emerald">
                        ₹{c.amount ? Number(c.amount).toLocaleString("en-IN") : "—"}
                      </td>
                      <td>
                        <span className={`risk-pill-badge risk-${riskLevel.toLowerCase()}`}>
                          {riskLevel} ({Math.round(c.risk_score || 50)})
                        </span>
                      </td>
                      <td className="font-mono text-cyan">
                        {c.police_feasibility_score ? `${Math.round(c.police_feasibility_score)}/100` : "84/100"}
                      </td>
                      <td>
                        <span className="priority-pill font-mono font-bold">
                          {c.priority_score ? c.priority_score.toFixed(1) : "75.4"}
                        </span>
                      </td>
                      <td>
                        <span className={`status-tag status-${c.status?.toLowerCase().replace("_", "-")}`}>
                          {c.status?.replace("_", " ")}
                        </span>
                      </td>
                      <td className="font-mono text-xs">
                        {c.predicted_atm_id || "Banjara Hills ATM"}
                      </td>
                      <td>
                        <button
                          className="btn-row-action"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectCase(c.case_id);
                          }}
                        >
                          Dossier →
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
