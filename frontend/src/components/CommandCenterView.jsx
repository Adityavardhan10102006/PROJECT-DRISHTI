import React, { useState, useEffect } from "react";
import { fetchCaseStats, fetchCases } from "../api.js";

export default function CommandCenterView({ onSelectCase, onNavigate }) {
  const [stats, setStats] = useState(null);
  const [priorityCases, setPriorityCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsData, casesData] = await Promise.all([
        fetchCaseStats(),
        fetchCases({ limit: 10 }),
      ]);
      setStats(statsData);
      setPriorityCases(casesData);
    } catch (err) {
      setError(err.message || "Failed to load command center data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const getRiskBadgeClass = (riskLevel) => {
    switch (riskLevel?.toUpperCase()) {
      case "CRITICAL":
        return "badge-critical";
      case "HIGH":
        return "badge-high";
      case "MEDIUM":
        return "badge-medium";
      default:
        return "badge-low";
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status?.toUpperCase()) {
      case "ACTION_REQUIRED":
        return "status-action-required";
      case "FIELD_ACTION":
        return "status-field-action";
      case "HIGH_PRIORITY":
        return "status-high-priority";
      case "RESOLVED":
        return "status-resolved";
      case "CLOSED":
        return "status-closed";
      default:
        return "status-new";
    }
  };

  return (
    <div className="command-center-container">
      {/* HEADER */}
      <div className="command-header">
        <div>
          <h1 className="command-title">PROJECT DRISHTI — COMMAND CENTER</h1>
          <p className="command-subtitle">
            Cybercrime Predictive Intelligence & Proactive Cash-Out Interception Framework
          </p>
        </div>
        <div className="command-header-actions">
          <span className="live-data-pill">
            <span className="live-dot pulse"></span>
            DATASET: HYDERABAD SYNTHETIC / REAL CANDIDATES
          </span>
          <button className="btn-refresh" onClick={loadData} title="Refresh Live Statistics">
            🔄 Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="command-error-banner">
          ⚠️ {error} — <button onClick={loadData} className="btn-link">Retry</button>
        </div>
      )}

      {/* KPI METRICS MATRIX */}
      <div className="kpi-grid">
        <div className="kpi-card kpi-total">
          <div className="kpi-label">ACTIVE INVESTIGATIONS</div>
          <div className="kpi-value">{stats ? stats.active_cases : "—"}</div>
          <div className="kpi-footer">Total Cases: {stats?.total_cases ?? "—"}</div>
        </div>

        <div className="kpi-card kpi-critical">
          <div className="kpi-label">CRITICAL RISK CASES</div>
          <div className="kpi-value text-red">{stats ? stats.critical_cases : "—"}</div>
          <div className="kpi-footer">High-Risk: {stats?.high_risk_cases ?? "—"}</div>
        </div>

        <div className="kpi-card kpi-action">
          <div className="kpi-label">ACTION REQUIRED</div>
          <div className="kpi-value text-amber">{stats ? stats.action_required : "—"}</div>
          <div className="kpi-footer">Field Action: {stats?.field_action ?? "—"}</div>
        </div>

        <div className="kpi-card kpi-accuracy">
          <div className="kpi-label">PREDICTION ACCURACY</div>
          <div className="kpi-value text-emerald">
            {stats && stats.prediction_accuracy_pct !== null
              ? `${stats.prediction_accuracy_pct}%`
              : "N/A"}
          </div>
          <div className="kpi-footer">
            {stats && stats.evaluated_outcomes > 0
              ? `${stats.successful_predictions} of ${stats.evaluated_outcomes} Verified`
              : "No verified outcomes yet"}
          </div>
        </div>
      </div>

      {/* TOP PRIORITY CASES TABLE */}
      <div className="panel-section">
        <div className="panel-header">
          <div className="panel-title-group">
            <span className="panel-icon">🎯</span>
            <div>
              <h2 className="panel-title">TOP PRIORITY INVESTIGATIONS</h2>
              <p className="panel-desc">
                Ranked by Composite Priority (0.60 × Risk + 0.40 × Police Feasibility)
              </p>
            </div>
          </div>
          <button className="btn-secondary" onClick={() => onNavigate("cases")}>
            View All Cases →
          </button>
        </div>

        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <span>Loading investigation dossiers...</span>
          </div>
        ) : priorityCases.length === 0 ? (
          <div className="empty-state">No investigation cases available.</div>
        ) : (
          <div className="table-responsive">
            <table className="drishti-table">
              <thead>
                <tr>
                  <th>CASE ID</th>
                  <th>RISK</th>
                  <th>PRIORITY</th>
                  <th>PREDICTED LOCATION</th>
                  <th>TIME WINDOW</th>
                  <th>AMOUNT</th>
                  <th>FEASIBILITY</th>
                  <th>STATUS</th>
                  <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {priorityCases.map((c) => (
                  <tr
                    key={c.case_id}
                    className="clickable-row"
                    onClick={() => onSelectCase(c.case_id)}
                  >
                    <td className="font-mono text-cyan">{c.case_id}</td>
                    <td>
                      <span className={`badge-pill ${getRiskBadgeClass(c.risk_level)}`}>
                        {c.risk_score ? `${c.risk_score}` : "—"} [{c.risk_level}]
                      </span>
                    </td>
                    <td>
                      <span className="priority-value font-mono">
                        {c.priority_score ? c.priority_score.toFixed(1) : "—"}
                      </span>
                    </td>
                    <td className="location-cell" title={c.predicted_area}>
                      📍 {c.predicted_area || "Hyderabad Area"}
                    </td>
                    <td className="font-mono">
                      {c.predicted_time_earliest_minutes && c.predicted_time_latest_minutes
                        ? `${c.predicted_time_earliest_minutes}–${c.predicted_time_latest_minutes} min`
                        : "—"}
                    </td>
                    <td className="font-mono font-bold">
                      ₹{Number(c.amount || 0).toLocaleString("en-IN")}
                    </td>
                    <td>
                      <span
                        className={`feasibility-pill ${
                          c.police_feasibility?.feasibility_status === "EXCELLENT_MARGIN"
                            ? "feas-excellent"
                            : "feas-moderate"
                        }`}
                      >
                        {c.police_feasibility?.feasibility_status || "AVAILABLE"}
                      </span>
                    </td>
                    <td>
                      <span className={`status-pill ${getStatusBadgeClass(c.status)}`}>
                        {c.status.replace("_", " ")}
                      </span>
                    </td>
                    <td>
                      <button
                        className="btn-inspect"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectCase(c.case_id);
                        }}
                      >
                        Investigate →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* QUICK OPERATIONAL WORKFLOW */}
      <div className="workflow-quick-bar">
        <div className="workflow-step" onClick={() => onNavigate("analyze")}>
          <div className="step-num">1</div>
          <div className="step-text">
            <strong>Intake & NLP</strong>
            <span>Analyze Complaint</span>
          </div>
        </div>
        <div className="workflow-arrow">→</div>
        <div className="workflow-step" onClick={() => onNavigate("trail")}>
          <div className="step-num">2</div>
          <div className="step-text">
            <strong>NetworkX Graph</strong>
            <span>Trace Money Trail</span>
          </div>
        </div>
        <div className="workflow-arrow">→</div>
        <div className="workflow-step" onClick={() => onNavigate("map")}>
          <div className="step-num">3</div>
          <div className="step-text">
            <strong>Geo Hotspots</strong>
            <span>Top-K ATM Map</span>
          </div>
        </div>
        <div className="workflow-arrow">→</div>
        <div className="workflow-step" onClick={() => onNavigate("models")}>
          <div className="step-num">4</div>
          <div className="step-text">
            <strong>Explainable AI</strong>
            <span>SHAP & 5D Signals</span>
          </div>
        </div>
        <div className="workflow-arrow">→</div>
        <div className="workflow-step" onClick={() => onNavigate("cases")}>
          <div className="step-num">5</div>
          <div className="step-text">
            <strong>Close the Loop</strong>
            <span>Record Outcome</span>
          </div>
        </div>
      </div>
    </div>
  );
}
