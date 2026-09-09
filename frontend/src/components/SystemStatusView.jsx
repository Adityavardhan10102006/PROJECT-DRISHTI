import React, { useState, useEffect } from "react";
import { fetchSystemStatus } from "../api.js";

export default function SystemStatusView() {
  const [statusData, setStatusData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSystemStatus();
      setStatusData(data);
    } catch (err) {
      setError(err.message || "Failed to query system status");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const getStatusPill = (val, goodVal = "ONLINE") => {
    const isGood = val === goodVal || val === "READY" || val === "AVAILABLE" || val === "LOADED";
    return (
      <span className={`status-indicator-pill ${isGood ? "ind-good" : "ind-bad"}`}>
        <span className="dot"></span>
        {val}
      </span>
    );
  };

  return (
    <div className="system-status-container">
      <div className="status-header">
        <div>
          <h1 className="status-title">SYSTEM STATUS & SUBSYSTEM DIAGNOSTICS</h1>
          <p className="status-subtitle">
            Infrastructure health, database readiness, dataset availability, and ML model runtime verification
          </p>
        </div>
        <button onClick={loadStatus} className="btn-refresh">
          🔄 Run Diagnostic Check
        </button>
      </div>

      {error && <div className="command-error-banner">⚠️ {error}</div>}

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <span>Polling subsystem endpoints...</span>
        </div>
      ) : !statusData ? (
        <div className="empty-state">Unable to communicate with DRISHTI diagnostic services.</div>
      ) : (
        <div className="diagnostics-matrix">
          <div className="diag-row">
            <div className="diag-item">
              <div className="diag-label">Core Backend Service (FastAPI)</div>
              <div className="diag-desc">HTTP application server and async lifespan runtime</div>
              <div className="diag-val">{getStatusPill(statusData.backend, "ONLINE")}</div>
            </div>

            <div className="diag-item">
              <div className="diag-label">Investigation Database (SQLite / ORM)</div>
              <div className="diag-desc">Relational cases, timeline events, and security audit store</div>
              <div className="diag-val">{getStatusPill(statusData.database, "READY")}</div>
            </div>
          </div>

          <div className="diag-row">
            <div className="diag-item">
              <div className="diag-label">Transaction Dataset (Static Demo)</div>
              <div className="diag-desc">data/transactions.csv — Multi-hop syndicate sequences</div>
              <div className="diag-val">{getStatusPill(statusData.transaction_dataset, "AVAILABLE")}</div>
            </div>

            <div className="diag-item">
              <div className="diag-label">ATM Candidate Geospatial Dataset</div>
              <div className="diag-desc">data/atms.csv — 181 Curated Hyderabad ATM terminals</div>
              <div className="diag-val">{getStatusPill(statusData.atm_dataset, "AVAILABLE")}</div>
            </div>
          </div>

          <div className="diag-row">
            <div className="diag-item">
              <div className="diag-label">Risk Classifier Model</div>
              <div className="diag-desc">models/risk_classifier.joblib (RandomForestClassifier)</div>
              <div className="diag-val">{getStatusPill(statusData.risk_model, "LOADED")}</div>
            </div>

            <div className="diag-item">
              <div className="diag-label">Cash-Out Amount Model</div>
              <div className="diag-desc">models/amount_predictor.joblib (GradientBoostingRegressor)</div>
              <div className="diag-val">{getStatusPill(statusData.amount_model, "LOADED")}</div>
            </div>
          </div>

          <div className="diag-row">
            <div className="diag-item">
              <div className="diag-label">Withdrawal Time Window Model</div>
              <div className="diag-desc">models/time_predictor.json (XGBoost Regressor)</div>
              <div className="diag-val">{getStatusPill(statusData.time_model, "LOADED")}</div>
            </div>

            <div className="diag-item">
              <div className="diag-label">Explainable AI (SHAP Engine)</div>
              <div className="diag-desc">shap.TreeExplainer feature attribution computation</div>
              <div className="diag-val">{getStatusPill(statusData.shap, "AVAILABLE")}</div>
            </div>
          </div>

          {/* SYSTEM PROVENANCE METADATA */}
          <div className="provenance-banner-box">
            <div className="prov-title">PROVENANCE & DATA INTEGRITY COMMITMENT</div>
            <p>
              Operating Mode: <strong>{statusData.data_mode}</strong>.
              All models run in local inference mode. Zero external cloud dependencies, zero fabricated coordinates,
              zero simulated police telemetry, and zero unverified real-time banking integrations.
            </p>
            <div className="prov-timestamp font-mono">
              Diagnostic Snapshot: {new Date(statusData.timestamp).toLocaleString()} | API Version: {statusData.version}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
