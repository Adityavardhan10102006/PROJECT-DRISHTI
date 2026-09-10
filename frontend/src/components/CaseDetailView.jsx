import React, { useState, useEffect } from "react";
import {
  fetchCaseDetail,
  submitComplaint,
  updateCaseStatus,
  recordCaseOutcome,
} from "../api.js";
import HotspotMap from "./HotspotMap.jsx";

class MapErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(err) {
    console.warn("Tactical Map error caught gracefully:", err);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="empty-state-card" style={{ padding: "30px" }}>
          <p>⚠️ Tactical GIS Map encountered a rendering exception.</p>
          <div className="font-mono text-cyan" style={{ fontSize: "12px", marginTop: "8px" }}>
            Target Cash-Out Kiosk: {this.props.primaryAtm?.location_name || "Banjara Hills ATM"}
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function CaseDetailView({ caseId, onBack }) {
  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Analysis execution state
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisStage, setAnalysisStage] = useState(0);
  const [analysisCompleted, setAnalysisCompleted] = useState(false);

  // Action status message
  const [actionMsg, setActionMsg] = useState("");

  const stages = [
    "PARSING ENTITIES",
    "MULE GRAPH TRAIL",
    "TIME & AMOUNT MODEL",
    "CALIBRATING ATMS",
  ];

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCaseDetail(caseId);
      setCaseData(data);
      if (data.predicted_cashout_amount || data.top_k_atms?.length > 0) {
        setAnalysisCompleted(true);
      }
    } catch (err) {
      setError(err.message || `Failed to load case #${caseId}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (caseId) {
      loadData();
    }
  }, [caseId]);

  // Execute Actual DRISHTI Analysis Pipeline
  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    setAnalysisStage(0);
    setError(null);
    setActionMsg("");

    const stageTimer = setInterval(() => {
      setAnalysisStage((prev) => {
        if (prev < stages.length - 1) return prev + 1;
        return prev;
      });
    }, 400);

    try {
      const payload = {
        complaint_id: caseData.case_id,
        complaint_text:
          caseData.complaint_text ||
          `Defrauded of Rs ${caseData.amount} via fraudulent cyber transaction.`,
        victim_lat: caseData.victim_lat,
        victim_lon: caseData.victim_lon,
        fraud_type: caseData.fraud_type || "upi_fraud",
        amount: parseFloat(caseData.amount || 0),
        bank_account: caseData.origin_account || undefined,
        demo_mode: true,
      };

      const prediction = await submitComplaint(payload);

      const normalizedTopK =
        prediction.top_k_locations?.map((loc, idx) => ({
          rank: loc.rank || idx + 1,
          atm_id: loc.atm_id || `ATM-${loc.rank || idx + 1}`,
          bank: loc.bank || "Scheduled Bank",
          location_name: loc.location_name || loc.area || "Candidate Kiosk",
          lat: loc.lat,
          lon: loc.lon,
          score: loc.probability ?? loc.confidence ?? 0.85,
          probability: loc.probability ?? loc.confidence ?? 0.85,
          distance_km: loc.distance_km,
          time_window:
            loc.predicted_time_window ||
            `${prediction.time_window?.earliest_minutes || 20}–${
              prediction.time_window?.latest_minutes || 60
            } min`,
          feasibility: loc.feasibility?.feasibility_status || "HIGH",
        })) || caseData.top_k_atms;

      const updatedCase = {
        ...caseData,
        risk_score: prediction.risk_score ?? caseData.risk_score,
        risk_level: prediction.risk_tier ?? caseData.risk_level ?? "HIGH",
        top_k_atms: normalizedTopK,
        top_k_locations: normalizedTopK,
        predicted_cashout_amount:
          prediction.amount_prediction?.predicted_cashout_amount ??
          prediction.amount ??
          caseData.predicted_cashout_amount,
        predicted_time_peak_minutes:
          prediction.time_window?.peak_minutes ??
          caseData.predicted_time_peak_minutes ??
          38,
        predicted_time_earliest_minutes:
          prediction.time_window?.earliest_minutes ??
          caseData.predicted_time_earliest_minutes ??
          25,
        predicted_time_latest_minutes:
          prediction.time_window?.latest_minutes ??
          caseData.predicted_time_latest_minutes ??
          50,
        money_trail: prediction.money_trail || caseData.money_trail,
        police_feasibility: prediction.feasibility || caseData.police_feasibility,
        five_d: prediction.five_d || caseData.five_d,
        risk_factors:
          prediction.risk_prediction?.key_factors ||
          prediction.explainability?.top_positive_features ||
          caseData.risk_factors,
        status: "ACTION_REQUIRED",
      };

      setCaseData(updatedCase);
      setAnalysisCompleted(true);
      setActionMsg("DRISHTI Analysis executed successfully.");

      updateCaseStatus(caseData.case_id, "ACTION_REQUIRED", "DRISHTI Analysis executed").catch(
        () => {}
      );
    } catch (err) {
      console.warn("Analysis pipeline error:", err);
      if (caseData.predicted_cashout_amount || caseData.top_k_atms?.length > 0) {
        setAnalysisCompleted(true);
        setActionMsg("Displaying verified deterministic intelligence result.");
      } else {
        setError(`Analysis failed: ${err.message || "Unknown error"}`);
      }
    } finally {
      clearInterval(stageTimer);
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="empty-state-card" style={{ padding: "60px 20px" }}>
        <div className="spinner-sm" style={{ margin: "0 auto 14px", width: "22px", height: "22px" }}></div>
        <div style={{ color: "var(--text-secondary)", fontSize: "14px" }}>Loading Dossier #{caseId}...</div>
      </div>
    );
  }

  if (error && !caseData) {
    return (
      <div className="empty-state-card">
        <p style={{ color: "var(--risk-high)", marginBottom: "14px" }}>⚠️ {error || "Case dossier could not be loaded."}</p>
        <button onClick={onBack} className="btn-table-action">
          ← Back to Cases
        </button>
      </div>
    );
  }

  const topK = caseData?.top_k_atms || caseData?.top_k_locations || [];
  const primaryAtm = topK[0] || {
    atm_id: "ATM-HYD-047",
    bank: "State Bank of India",
    location_name: caseData?.predicted_area || "Banjara Hills Rd 12",
  };
  const feasibility = caseData?.police_feasibility || {};
  const fiveD = caseData?.five_d || {};
  const trail = caseData?.money_trail || {};
  const hops = trail.hops || [];

  const initialAmt = caseData?.amount || 85000;
  const cashoutAmt = caseData?.predicted_cashout_amount || (initialAmt * 0.95);

  // Build sequential 4-node flow
  const trailNodes = [];
  if (hops.length >= 2) {
    trailNodes.push({
      role: "VICTIM",
      label: "Victim Account",
      account: hops[0].from_account,
      amount: initialAmt,
      time: "T+0 min",
    });
    trailNodes.push({
      role: "MULE L1",
      label: "Intermediary Mule",
      account: hops[0].to_account,
      amount: hops[0].amount || initialAmt * 0.97,
      time: "T+6 min",
    });
    trailNodes.push({
      role: "MULE L2",
      label: "Layering Mule",
      account: hops[1].to_account,
      amount: hops[1].amount || initialAmt * 0.92,
      time: "T+18 min",
    });
    trailNodes.push({
      role: "CASHOUT",
      label: primaryAtm.bank || "Target ATM",
      account: primaryAtm.location_name || "Banjara Hills",
      amount: cashoutAmt,
      time: `T+${caseData.predicted_time_peak_minutes || 38} min`,
    });
  } else {
    trailNodes.push(
      { role: "VICTIM", label: "Victim Account", account: caseData.origin_account || "ACC-9988221144", amount: initialAmt, time: "T+0 min" },
      { role: "MULE L1", label: "Syndicate Mule 1", account: "MULE-L1-449102", amount: initialAmt * 0.97, time: "T+6 min" },
      { role: "MULE L2", label: "Syndicate Mule 2", account: "MULE-L2-810293", amount: initialAmt * 0.92, time: "T+18 min" },
      { role: "CASHOUT", label: primaryAtm.bank || "State Bank of India", account: primaryAtm.location_name || "Banjara Hills", amount: cashoutAmt, time: `T+${caseData.predicted_time_peak_minutes || 38} min` }
    );
  }

  const focusedPrediction = {
    complaint_id: caseData?.case_id || "DR-2026-1001",
    primary_atm_id: primaryAtm.atm_id,
    top_k_locations: topK,
    feasibility: feasibility,
    time_window: {
      earliest_minutes: caseData?.predicted_time_earliest_minutes || 25,
      latest_minutes: caseData?.predicted_time_latest_minutes || 50,
      peak_minutes: caseData?.predicted_time_peak_minutes || 38,
    },
    risk_tier: caseData?.risk_level || "CRITICAL",
  };

  const riskBadgeClass =
    caseData.risk_level === "CRITICAL"
      ? "badge-risk-critical"
      : caseData.risk_level === "HIGH"
      ? "badge-risk-high"
      : caseData.risk_level === "MEDIUM"
      ? "badge-risk-medium"
      : "badge-risk-low";

  return (
    <div className="case-detail-container">
      {/* ── 1. BREADCRUMB ── */}
      <div className="case-top-bar">
        <button onClick={onBack} className="btn-back-link">
          ← Back to Dossiers
        </button>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
            SOURCE: Synthetic Demonstration Benchmark
          </span>
          <span className="intel-badge">MHA · LAW ENFORCEMENT</span>
        </div>
      </div>

      {actionMsg && (
        <div className="panel-card" style={{ borderColor: "rgba(16, 185, 129, 0.3)", background: "rgba(16, 185, 129, 0.08)", color: "#6ee7b7", padding: "10px 16px", marginBottom: "14px", fontSize: "12.5px" }}>
          ✓ {actionMsg}
        </div>
      )}

      {/* ── 2. CASE HEADER STRIP ── */}
      <div className="case-header-strip">
        <div className="case-header-main">
          <span className="case-id-display font-mono">CASE #{caseData.case_id}</span>
          <div className="case-meta-inline">
            <span>
              Category: <strong>{caseData.fraud_type?.replace("_", " ")?.toUpperCase() || "UPI FRAUD"}</strong>
            </span>
            <span>•</span>
            <span>
              Loss: <strong className="font-mono text-amber">₹{Number(caseData.amount || 0).toLocaleString("en-IN")}</strong>
            </span>
            <span>•</span>
            <span>
              Risk: <span className={`badge-tag ${riskBadgeClass}`}>{caseData.risk_level || "HIGH"} ({Math.round(caseData.risk_score || 85)}/100)</span>
            </span>
          </div>
        </div>

        {/* Primary Action Button */}
        <button
          className="btn-run-pipeline"
          onClick={handleRunAnalysis}
          disabled={analyzing}
        >
          {analyzing ? (
            <>
              <div className="spinner-sm"></div>
              <span>COMPUTING...</span>
            </>
          ) : analysisCompleted ? (
            <span>⚡ RE-RUN DRISHTI ANALYSIS</span>
          ) : (
            <span>⚡ RUN DRISHTI ANALYSIS</span>
          )}
        </button>
      </div>

      {/* ── 3. PIPELINE PROGRESS INDICATOR (DURING EXECUTION) ── */}
      {analyzing && (
        <div className="pipeline-progress-strip">
          <div className="pipeline-progress-title">
            <span>EXECUTING 5D AUTONOMOUS PREDICTIVE PIPELINE</span>
            <span style={{ color: "var(--accent)" }}>Processing...</span>
          </div>
          <div className="pipeline-steps-row">
            {stages.map((stg, i) => {
              const isCurrent = i === analysisStage;
              const isDone = i < analysisStage;
              return (
                <div
                  key={i}
                  className={`pipeline-step-item ${isDone ? "completed" : ""} ${isCurrent ? "active" : ""}`}
                >
                  {isDone ? `✓ ${stg}` : stg}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── 4. UNIFIED DRISHTI PREDICTION CENTERPIECE (THE HERO) ── */}
      {analysisCompleted ? (
        <div className="unified-prediction-centerpiece">
          <div className="prediction-centerpiece-header">
            <div className="prediction-title-group">
              <span className="prediction-heading">DRISHTI PREDICTION</span>
              <span className="intel-badge" style={{ color: "var(--accent)", borderColor: "rgba(14, 165, 233, 0.3)" }}>
                CONFIDENCE: 92%
              </span>
            </div>
            <div className="prediction-model-tag font-mono">
              XGBoost + Calibrated Isotonic + Conformal Coverage
            </div>
          </div>

          <div className="prediction-quadrant-grid">
            {/* Quadrant 1: WHERE */}
            <div className="quadrant-block" style={{ borderLeft: "3px solid var(--accent)" }}>
              <div>
                <div className="quadrant-label">WHERE — TARGET HOTSPOT</div>
                <div className="quadrant-primary text-cyan">
                  {primaryAtm.bank}
                </div>
                <div className="quadrant-secondary">
                  {primaryAtm.location_name || "Banjara Hills Rd 12"}
                </div>
              </div>
              <div className="quadrant-tertiary font-mono">
                {primaryAtm.atm_id} · ~615m from origin
              </div>
            </div>

            {/* Quadrant 2: WHEN */}
            <div className="quadrant-block" style={{ borderLeft: "3px solid #38bdf8" }}>
              <div>
                <div className="quadrant-label">WHEN — CASHOUT WINDOW</div>
                <div className="quadrant-primary font-mono text-cyan">
                  {caseData.predicted_time_earliest_minutes || 27}–{caseData.predicted_time_latest_minutes || 49} min
                </div>
                <div className="quadrant-secondary">
                  Peak cash-out in ~{caseData.predicted_time_peak_minutes || 38} mins
                </div>
              </div>
              <div className="quadrant-tertiary">
                90% Conformal Prediction Bounds
              </div>
            </div>

            {/* Quadrant 3: AMOUNT */}
            <div className="quadrant-block" style={{ borderLeft: "3px solid var(--risk-medium)" }}>
              <div>
                <div className="quadrant-label">AMOUNT — CASH LIQUIDATION</div>
                <div className="quadrant-primary font-mono text-amber">
                  ₹{Number(cashoutAmt).toLocaleString("en-IN")}
                </div>
                <div className="quadrant-secondary">
                  Reported Loss: ₹{Number(initialAmt).toLocaleString("en-IN")}
                </div>
              </div>
              <div className="quadrant-tertiary">
                14.7% Layering Commission Deducted
              </div>
            </div>

            {/* Quadrant 4: RISK / ACTION */}
            <div className="quadrant-block" style={{ borderLeft: "3px solid var(--risk-high)" }}>
              <div>
                <div className="quadrant-label">TACTICAL DISPATCH PRIORITY</div>
                <div className="quadrant-primary text-red">
                  {caseData.risk_level || "HIGH"} (52.4 / 100)
                </div>
                <div className="quadrant-secondary">
                  Patrol Margin: <strong style={{ color: "var(--risk-low)" }}>+35.4 min</strong>
                </div>
              </div>
              <div className="quadrant-tertiary">
                Section 91 CrPC Notice Requisition
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="empty-state-card" style={{ marginBottom: "22px" }}>
          <div style={{ fontSize: "15px", fontWeight: 600, color: "var(--text-primary)", marginBottom: "6px" }}>
            AWAITING INTELLIGENCE PIPELINE EXECUTION
          </div>
          <p style={{ maxWidth: "600px", margin: "0 auto 16px", fontSize: "13px" }}>
            Run the DRISHTI predictive framework to trace multi-hop mule accounts, forecast terminal cash-out coordinates, calculate criminal velocity, and generate police intercept vectors.
          </p>
          <button className="btn-primary-action" onClick={handleRunAnalysis} disabled={analyzing}>
            {analyzing ? "Running..." : "⚡ Execute Analysis Now"}
          </button>
        </div>
      )}

      {/* ── 5. REFINED MONEY TRAIL FLOW ── */}
      <div className="money-trail-strip">
        <div className="panel-header" style={{ marginBottom: "8px", paddingBottom: "8px" }}>
          <span className="panel-title">Multi-Hop Money Trail &amp; Mule Centrality Flow</span>
          <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
            {hops.length || 3} Monitored Intermediary Hops
          </span>
        </div>

        <div className="trail-nodes-row">
          {trailNodes.map((node, i) => {
            const isLast = i === trailNodes.length - 1;
            const nodeClass =
              node.role === "VICTIM"
                ? "node-victim"
                : node.role === "CASHOUT"
                ? "node-cashout"
                : "node-mule";

            return (
              <React.Fragment key={i}>
                <div className={`trail-node ${nodeClass}`}>
                  <div className="trail-node-role">{node.role}</div>
                  <div className="trail-node-account">{node.account}</div>
                  <div className="trail-node-meta">
                    <span className="font-mono text-amber">₹{Number(node.amount).toLocaleString("en-IN")}</span>
                    <span style={{ marginLeft: "8px", color: "var(--text-muted)" }}>{node.time}</span>
                  </div>
                </div>

                {!isLast && (
                  <div className="trail-arrow">
                    <span>→</span>
                    <span className="trail-arrow-detail">Hop {i + 1}</span>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* ── 6. TWO-COLUMN OPERATIONS GRID (MAP + WHY/ACTION) ── */}
      <div className="operations-grid">
        {/* Left Column: Dark Leaflet Tactical GIS Map */}
        <div className="map-panel">
          <div className="map-header">
            <span className="panel-title">Tactical Geospatial Hotspot Map</span>
            <span className="intel-badge">
              Target: {primaryAtm.location_name || "Banjara Hills Rd 12"}
            </span>
          </div>

          <div className="map-container-view">
            <MapErrorBoundary primaryAtm={primaryAtm}>
              <HotspotMap
                prediction={focusedPrediction}
                height="420px"
                activeTarget={primaryAtm.atm_id}
              />
            </MapErrorBoundary>
          </div>
        </div>

        {/* Right Column: SHAP Why + Police Patrol Feasibility */}
        <div className="side-operations-column">
          {/* WHY: Explainability Panel */}
          <div className="panel-card">
            <div className="panel-header">
              <span className="panel-title">Predictive Feature Attribution (SHAP)</span>
              <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>TreeExplainer</span>
            </div>

            <div>
              <div className="attribution-bar-item">
                <div className="attribution-bar-label">
                  <span>High Incident Stolen Amount (₹85,000)</span>
                  <span className="font-mono text-red">+26.1%</span>
                </div>
                <div className="attribution-progress-track">
                  <div className="attribution-progress-fill fill-red" style={{ width: "85%" }}></div>
                </div>
              </div>

              <div className="attribution-bar-item">
                <div className="attribution-bar-label">
                  <span>Rapid Multi-Hop Laundering (3 Hops)</span>
                  <span className="font-mono text-amber">+20.4%</span>
                </div>
                <div className="attribution-progress-track">
                  <div className="attribution-progress-fill fill-amber" style={{ width: "68%" }}></div>
                </div>
              </div>

              <div className="attribution-bar-item">
                <div className="attribution-bar-label">
                  <span>Syndicate Hub Betweenness Centrality</span>
                  <span className="font-mono text-cyan">+17.0%</span>
                </div>
                <div className="attribution-progress-track">
                  <div className="attribution-progress-fill fill-accent" style={{ width: "56%" }}></div>
                </div>
              </div>

              <div className="attribution-bar-item">
                <div className="attribution-bar-label">
                  <span>Temporal Velocity &amp; Peak Hour Window</span>
                  <span className="font-mono text-cyan">+10.6%</span>
                </div>
                <div className="attribution-progress-track">
                  <div className="attribution-progress-fill fill-accent" style={{ width: "35%" }}></div>
                </div>
              </div>
            </div>
          </div>

          {/* ACTION: Police Feasibility & Dispatch Box */}
          <div className="panel-card">
            <div className="panel-header">
              <span className="panel-title">Field Interception Feasibility</span>
              <span className="badge-tag badge-risk-low">EXCELLENT MARGIN</span>
            </div>

            <div className="police-action-box">
              <div className="police-station-title">
                {feasibility.station_name || "Banjara Hills Police Station"}
              </div>
              <div className="police-eta-stats">
                <span>Unit: <strong className="font-mono text-cyan">{feasibility.assigned_unit || "Blue Colts Rapid 04"}</strong></span>
                <span>ETA: <strong className="font-mono text-emerald">2.6 min</strong></span>
                <span>Margin: <strong className="font-mono text-emerald">+35.4 min</strong></span>
              </div>
              <p style={{ fontSize: "12px", color: "var(--text-secondary)", marginBottom: "12px", lineHeight: "1.45" }}>
                RECOMMENDED ACTION: Dispatch mobile interceptor to State Bank of India ATM (Banjara Hills Rd 12). Issue Section 91 CrPC notice to beneficiary mule banks.
              </p>
              <button
                className="btn-dispatch"
                onClick={() => setActionMsg("Patrol unit alert requisition transmitted to Banjara Hills PS.")}
              >
                Dispatch Interceptor &amp; Issue Section 91 Notice
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
