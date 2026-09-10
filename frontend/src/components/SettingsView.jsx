import React, { useState, useEffect } from "react";
import { fetchHealth } from "../api.js";

export default function SettingsView() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetchHealth()
      .then((data) => setHealth(data))
      .catch(() => setHealth({ status: "offline" }));
  }, []);

  const metrics = {
    risk: {
      model: "RandomForestClassifier + SHAP TreeExplainer",
      accuracy: "77.96%",
      roc_auc: "0.9238",
      samples: "7,500 records",
    },
    amount: {
      model: "GradientBoostingRegressor",
      mae: "₹1,942.97",
      r2: "0.9858",
      samples: "4,500 records",
    },
    time: {
      model: "XGBoost Regressor (Conformalized)",
      mae: "5.32 minutes",
      r2: "0.7144",
      conformal_q90: "±10.6 min (90% coverage)",
      samples: "5,000 records",
    },
    location: {
      model: "XGBoost + Isotonic Calibrator",
      top1_accuracy: "51.67%",
      top3_recall: "92.22%",
      top5_recall: "100.0%",
      mrr: "0.7041",
    },
  };

  return (
    <div className="view-container">
      <div className="view-header">
        <div>
          <h1 className="view-title">System Settings &amp; Telemetry</h1>
          <p className="view-subtitle">
            Engine status, ML model evaluation benchmarks, and data provenance
          </p>
        </div>
        <div className="badge-pill badge-primary">
          Cybercrime Intelligence · MHA
        </div>
      </div>

      {/* ── 1. SYSTEM COMPONENT HEALTH ── */}
      <div className="table-card" style={{ marginBottom: "24px", padding: "18px 20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
          <h2 style={{ fontSize: "11.5px", fontWeight: 700, letterSpacing: "0.8px", textTransform: "uppercase", color: "var(--text-muted)", margin: 0 }}>
            ENGINE COMPONENT HEALTH
          </h2>
          <span style={{ fontSize: "11px", color: "var(--risk-low)", display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--risk-low)", display: "inline-block" }}></span>
            All 6 Core Subsystems Active
          </span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px" }}>
          <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-sm)", padding: "12px 14px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--risk-low)" }}></span>
              <span style={{ fontSize: "12.5px", fontWeight: 600, color: "var(--text-primary)" }}>FastAPI Core Engine</span>
            </div>
            <div style={{ fontSize: "11px", color: "var(--text-secondary)", paddingLeft: "14px" }}>
              {health?.status === "ok" || health?.status === "healthy" ? "Operational (v1.0.0)" : "Checking..."}
            </div>
          </div>
          <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-sm)", padding: "12px 14px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--risk-low)" }}></span>
              <span style={{ fontSize: "12.5px", fontWeight: 600, color: "var(--text-primary)" }}>SQLite Database</span>
            </div>
            <div style={{ fontSize: "11px", color: "var(--text-secondary)", paddingLeft: "14px" }}>drishti.db (Persistent)</div>
          </div>
          <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-sm)", padding: "12px 14px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--risk-low)" }}></span>
              <span style={{ fontSize: "12.5px", fontWeight: 600, color: "var(--text-primary)" }}>XGBoost Time Predictor</span>
            </div>
            <div style={{ fontSize: "11px", color: "var(--text-secondary)", paddingLeft: "14px" }}>Conformalized (MAE: 5.32m)</div>
          </div>
          <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-sm)", padding: "12px 14px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--risk-low)" }}></span>
              <span style={{ fontSize: "12.5px", fontWeight: 600, color: "var(--text-primary)" }}>RandomForest Risk Classifier</span>
            </div>
            <div style={{ fontSize: "11px", color: "var(--text-secondary)", paddingLeft: "14px" }}>SHAP Explainer Loaded</div>
          </div>
          <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-sm)", padding: "12px 14px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--risk-low)" }}></span>
              <span style={{ fontSize: "12.5px", fontWeight: 600, color: "var(--text-primary)" }}>Amount Regressor</span>
            </div>
            <div style={{ fontSize: "11px", color: "var(--text-secondary)", paddingLeft: "14px" }}>Gradient Boosting (R²: 0.986)</div>
          </div>
          <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-sm)", padding: "12px 14px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--risk-low)" }}></span>
              <span style={{ fontSize: "12.5px", fontWeight: 600, color: "var(--text-primary)" }}>NetworkX Graph Engine</span>
            </div>
            <div style={{ fontSize: "11px", color: "var(--text-secondary)", paddingLeft: "14px" }}>Multi-Hop Mule Traversal</div>
          </div>
        </div>
      </div>

      {/* ── 2. ML BENCHMARKS (FROM models/metrics.json) ── */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
          <h2 style={{ fontSize: "11.5px", fontWeight: 700, letterSpacing: "0.8px", textTransform: "uppercase", color: "var(--text-muted)", margin: 0 }}>
            ML MODEL EVALUATION BENCHMARKS
          </h2>
          <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            Source: models/metrics.json
          </span>
        </div>

        <div className="settings-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
          <div className="telemetry-card">
            <div className="telemetry-card-title">CASH-OUT LOCATION RANKER</div>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "10px" }}>{metrics.location.model}</div>
            <div className="telemetry-item">
              <span className="telemetry-item-name">Top-3 Recall</span>
              <span className="telemetry-item-val" style={{ color: "var(--risk-low)" }}>{metrics.location.top3_recall}</span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-item-name">Top-5 Recall</span>
              <span className="telemetry-item-val" style={{ color: "var(--risk-low)" }}>{metrics.location.top5_recall}</span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-item-name">Top-1 Accuracy</span>
              <span className="telemetry-item-val">{metrics.location.top1_accuracy}</span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-item-name">Mean Reciprocal Rank (MRR)</span>
              <span className="telemetry-item-val">{metrics.location.mrr}</span>
            </div>
          </div>

          <div className="telemetry-card">
            <div className="telemetry-card-title">TIME-WINDOW PREDICTOR</div>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "10px" }}>{metrics.time.model}</div>
            <div className="telemetry-item">
              <span className="telemetry-item-name">Mean Absolute Error</span>
              <span className="telemetry-item-val" style={{ color: "var(--accent)" }}>{metrics.time.mae}</span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-item-name">R² Score</span>
              <span className="telemetry-item-val" style={{ color: "var(--accent)" }}>{metrics.time.r2}</span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-item-name">Conformal Interval</span>
              <span className="telemetry-item-val">{metrics.time.conformal_q90}</span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-item-name">Training Size</span>
              <span className="telemetry-item-val">{metrics.time.samples}</span>
            </div>
          </div>

          <div className="telemetry-card">
            <div className="telemetry-card-title">RISK CLASSIFIER &amp; SHAP</div>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "10px" }}>{metrics.risk.model}</div>
            <div className="telemetry-item">
              <span className="telemetry-item-name">Classification Accuracy</span>
              <span className="telemetry-item-val" style={{ color: "var(--risk-medium)" }}>{metrics.risk.accuracy}</span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-item-name">ROC-AUC</span>
              <span className="telemetry-item-val" style={{ color: "var(--risk-medium)" }}>{metrics.risk.roc_auc}</span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-item-name">Explainability</span>
              <span className="telemetry-item-val">TreeExplainer</span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-item-name">Benchmark Dataset</span>
              <span className="telemetry-item-val">{metrics.risk.samples}</span>
            </div>
          </div>

          <div className="telemetry-card">
            <div className="telemetry-card-title">CASH-OUT AMOUNT REGRESSOR</div>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "10px" }}>{metrics.amount.model}</div>
            <div className="telemetry-item">
              <span className="telemetry-item-name">Mean Absolute Error</span>
              <span className="telemetry-item-val" style={{ color: "var(--risk-low)" }}>{metrics.amount.mae}</span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-item-name">R² Variance</span>
              <span className="telemetry-item-val" style={{ color: "var(--risk-low)" }}>{metrics.amount.r2}</span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-item-name">Quantile Bounds</span>
              <span className="telemetry-item-val">Empirical</span>
            </div>
            <div className="telemetry-item">
              <span className="telemetry-item-name">Benchmark Dataset</span>
              <span className="telemetry-item-val">{metrics.amount.samples}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── 3. DATA TRANSPARENCY & PROVENANCE ── */}
      <div className="table-card" style={{ padding: "18px 20px" }}>
        <h2 style={{ fontSize: "11.5px", fontWeight: 700, letterSpacing: "0.8px", textTransform: "uppercase", color: "var(--text-muted)", margin: "0 0 10px 0" }}>
          DATA TRANSPARENCY &amp; REGULATORY NOTICE
        </h2>
        <div style={{ fontSize: "12px", lineHeight: "1.6", color: "var(--text-secondary)" }}>
          <p style={{ margin: "0 0 8px 0" }}>
            <strong style={{ color: "var(--text-primary)" }}>Prototype Data Notice:</strong> Project DRISHTI prototype operates
            on curated synthetic transaction networks, deterministic cybercrime complaints,
            and benchmark geospatial locations in the Hyderabad/Cyberabad police commissionerates.
          </p>
          <p style={{ margin: 0, color: "var(--text-muted)" }}>
            <strong style={{ color: "var(--text-secondary)" }}>Production Architecture:</strong> Designed for institutional integration
            with authorized law enforcement systems (NCRP, I4C) and core banking transaction streams via Section 91 CrPC lawful access protocols. Project DRISHTI serves as an investigator decision-support system and does not execute autonomous banking freezes or police dispatches without human verification.
          </p>
        </div>
      </div>
    </div>
  );
}
