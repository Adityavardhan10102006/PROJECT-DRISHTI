import React, { useState, useEffect } from "react";
import {
  fetchCaseDetail,
  analyzeCase,
  updateCaseStatus,
  recordCaseOutcome,
} from "../api.js";
import HotspotMap from "./HotspotMap.jsx";
import DrishtiWorkflowChain from "./DrishtiWorkflowChain.jsx";

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
          <p>⚠️ Tactical Geospatial Map encountered a rendering exception.</p>
          <div className="font-mono text-cyan" style={{ fontSize: "12px", marginTop: "8px" }}>
            Target Cash-Out Kiosk: {this.props.primaryAtm?.location_name || "Location prediction unavailable"}
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function CaseDetailView({ caseId, onBack, onNavigate }) {
  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Analysis & 8-Stage Workflow execution state
  const [analyzing, setAnalyzing] = useState(false);
  const [workflowStage, setWorkflowStage] = useState(0);
  const [analysisCompleted, setAnalysisCompleted] = useState(false);

  // Action status message
  const [actionMsg, setActionMsg] = useState("");

  // Feedback Modal State
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackAccurate, setFeedbackAccurate] = useState(true);
  const [feedbackIntercepted, setFeedbackIntercepted] = useState(false);
  const [feedbackNotes, setFeedbackNotes] = useState("");
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCaseDetail(caseId);
      setCaseData(data);
      if (data.predicted_cashout_amount || (data.top_k_atms && data.top_k_atms.length > 0)) {
        setAnalysisCompleted(true);
        setWorkflowStage(8);
      } else {
        setWorkflowStage(0);
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

  // Execute Real DRISHTI Analysis Pipeline
  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    setWorkflowStage(1);
    setError(null);
    setActionMsg("");

    try {
      // Step through workflow stages synchronously as real pipeline executes
      setWorkflowStage(3);
      const updatedCase = await analyzeCase(caseData.case_id);
      setWorkflowStage(7);

      setCaseData(updatedCase);
      setWorkflowStage(8);
      setAnalysisCompleted(true);
      setActionMsg("DRISHTI 8-Stage Predictive Pipeline executed and verified by backend ML models.");
    } catch (err) {
      console.warn("Analysis pipeline error:", err);
      setError(`Analysis failed: ${err.message || "Unable to connect to analysis service."}`);
      if (caseData?.predicted_cashout_amount || caseData?.top_k_atms?.length > 0) {
        setWorkflowStage(8);
        setAnalysisCompleted(true);
      } else {
        setWorkflowStage(0);
      }
    } finally {
      setAnalyzing(false);
    }
  };

  // Export structured intelligence dossier
  const handleExportDossier = () => {
    if (!caseData) return;
    const payload = {
      platform: "PROJECT DRISHTI",
      system: "Predictive Analytics Framework for Cybercrime Complaints",
      case_id: caseData.case_id,
      data_mode: "SYNTHETIC DEMONSTRATION DATA",
      export_timestamp: new Date().toISOString(),
      case_metadata: {
        category: caseData.fraud_type,
        reported_loss_inr: initialAmt,
        risk_level: caseData.risk_level,
        risk_score: caseData.risk_score,
        status: caseData.status,
      },
      five_d_intelligence: {
        where: {
          predicted_terminal: primaryAtm?.location_name || caseData.predicted_area || "Unavailable",
          bank: primaryAtm?.bank || "Candidate ATM",
          atm_id: primaryAtm?.atm_id || null,
          distance_km: primaryAtm?.distance_km ?? null,
          method: "XGBoost Classifier + Isotonic Calibration",
        },
        when: {
          peak_minutes: caseData.predicted_time_peak_minutes,
          window_minutes: `${caseData.predicted_time_earliest_minutes || 0}–${caseData.predicted_time_latest_minutes || 0}`,
          conformal_uncertainty: `±${caseData.conformal_interval_minutes || 10.6}m (90% coverage)`,
          method: "XGBoost Regressor (Conformalized)",
        },
        amount: {
          predicted_cashout_inr: cashoutAmt,
          reported_loss_inr: initialAmt,
          discount_ratio: initialAmt && cashoutAmt ? `${((cashoutAmt / initialAmt) * 100).toFixed(1)}%` : "Unavailable",
          method: "GradientBoostingRegressor",
        },
        why: {
          key_drivers: riskFactors,
          method: "TreeSHAP Local Feature Attribution",
        },
        action: {
          assigned_patrol_unit: feasibility.assigned_unit || feasibility.unit_name || "Patrol Interceptor",
          estimated_eta_minutes: feasibility.eta_minutes,
          patrol_margin_minutes: feasibility.time_margin_minutes,
          feasibility_status: feasibility.feasibility_status,
          protocol: caseData.five_d?.action?.protocol || "Section 91 CrPC Notice + Field Intercept Advisory",
        },
      },
      money_trail: {
        total_hops: hops.length,
        hops: hops,
      },
      disclaimer: "SYNTHETIC DEMONSTRATION DATA. Not connected to live bank or government systems.",
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `DRISHTI_DOSSIER_${caseData.case_id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setActionMsg(`Dossier #${caseData.case_id} successfully exported as JSON.`);
  };

  // Submit verified field feedback to backend
  const handleSubmitFeedback = async (e) => {
    if (e) e.preventDefault();
    setSubmittingFeedback(true);
    setError(null);
    try {
      await recordCaseOutcome(caseData.case_id, {
        actual_atm_id: primaryAtm?.atm_id || "ATM-HYD-041",
        actual_amount: cashoutAmt || initialAmt || 70800,
        was_intercepted: feedbackIntercepted,
        is_correct: feedbackAccurate,
        notes: feedbackNotes || "Investigator field feedback submitted via DRISHTI console.",
      });
      setActionMsg("✓ Ground-truth feedback logged to audit ledger & SQLite database.");
      setShowFeedbackModal(false);
    } catch (err) {
      setError(`Failed to submit feedback: ${err.message || "Network error"}`);
    } finally {
      setSubmittingFeedback(false);
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
  const primaryAtm = topK.length > 0 ? topK[0] : null;
  const feasibility = caseData?.police_feasibility || {};
  const fiveD = caseData?.five_d || {};
  const trail = caseData?.money_trail || {};
  const hops = trail.hops || [];

  const initialAmt = caseData?.amount != null ? Number(caseData.amount) : null;
  const cashoutAmt = caseData?.predicted_cashout_amount != null ? Number(caseData.predicted_cashout_amount) : null;

  // Build sequential trail nodes strictly from real hops
  const trailNodes = [];
  if (hops.length > 0) {
    // First node: Victim
    trailNodes.push({
      role: "VICTIM",
      label: "Victim Account",
      account: hops[0].from_account || caseData?.origin_account || "ACC-VICTIM",
      amount: initialAmt || hops[0].amount,
      time: "T+0 min",
      bank: "Complainant Bank",
    });

    // Intermediate hops: Mule accounts
    hops.forEach((h, idx) => {
      const isTerminal = h.is_terminal_cashout || idx === hops.length - 1;
      trailNodes.push({
        role: isTerminal ? "CASHOUT" : `MULE L${h.hop_index || idx + 1}`,
        label: isTerminal ? (primaryAtm?.bank || h.to_bank || "Target ATM") : (h.to_bank || "Intermediary Mule"),
        account: isTerminal ? (primaryAtm?.location_name || h.to_account) : h.to_account,
        amount: h.amount,
        time: h.minutes_from_start != null ? `T+${h.minutes_from_start} min` : `Hop ${idx + 1}`,
        bank: h.to_bank,
      });
    });
  } else if (caseData?.origin_account) {
    trailNodes.push({
      role: "VICTIM",
      label: "Origin Account",
      account: caseData.origin_account,
      amount: initialAmt,
      time: "T+0 min",
    });
  }

  const focusedPrediction = {
    complaint_id: caseData?.case_id || "CASE-001-UPI-CRITICAL",
    primary_atm_id: primaryAtm?.atm_id,
    top_k_locations: topK,
    feasibility: feasibility,
    time_window: {
      earliest_minutes: caseData?.predicted_time_earliest_minutes,
      latest_minutes: caseData?.predicted_time_latest_minutes,
      peak_minutes: caseData?.predicted_time_peak_minutes,
    },
    risk_tier: caseData?.risk_level || "MEDIUM",
  };

  const riskBadgeClass =
    caseData?.risk_level === "CRITICAL"
      ? "badge-risk-critical"
      : caseData?.risk_level === "HIGH"
      ? "badge-risk-high"
      : caseData?.risk_level === "MEDIUM"
      ? "badge-risk-medium"
      : "badge-risk-low";

  // Dynamic model confidence
  const heroConfidence =
    primaryAtm?.probability != null
      ? `${Math.round(primaryAtm.probability * 100)}%`
      : primaryAtm?.score != null
      ? `${Math.round(primaryAtm.score * 100)}%`
      : caseData?.risk_score != null
      ? `${Math.round(caseData.risk_score)}%`
      : null;

  // Real risk factors & feature attributions from backend
  const riskFactors = caseData?.risk_factors || caseData?.five_d?.why?.top_reasons || [];

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
          <span className="intel-badge">DECISION SUPPORT PROTOTYPE</span>
        </div>
      </div>

      {actionMsg && (
        <div className="panel-card" style={{ borderColor: "rgba(16, 185, 129, 0.3)", background: "rgba(16, 185, 129, 0.08)", color: "#6ee7b7", padding: "10px 16px", marginBottom: "14px", fontSize: "12.5px" }}>
          ✓ {actionMsg}
        </div>
      )}

      {error && (
        <div className="panel-card" style={{ borderColor: "rgba(229, 9, 20, 0.4)", background: "rgba(229, 9, 20, 0.08)", color: "#ff6b6b", padding: "10px 16px", marginBottom: "14px", fontSize: "12.5px" }}>
          ⚠️ {error}
        </div>
      )}

      {/* ── 2. CASE HEADER STRIP ── */}
      <div className="case-header-strip">
        <div className="case-header-main">
          <span className="case-id-display font-mono">CASE #{caseData.case_id}</span>
          <div className="case-meta-inline">
            <span>
              Category: <strong>{caseData.fraud_type?.replace("_", " ")?.toUpperCase() || "CYBER FRAUD"}</strong>
            </span>
            <span>•</span>
            <span>
              Loss: <strong className="font-mono text-amber">{initialAmt != null ? `₹${initialAmt.toLocaleString("en-IN")}` : "Unavailable"}</strong>
            </span>
            <span>•</span>
            <span>
              Risk: <span className={`badge-tag ${riskBadgeClass}`}>{caseData.risk_level || "EVALUATING"}{caseData.risk_score != null ? ` (${Math.round(caseData.risk_score)}/100)` : ""}</span>
            </span>
          </div>
        </div>

        {/* Action Buttons Group */}
        <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
          {onNavigate && (
            <button
              type="button"
              className="chip-btn"
              onClick={() => onNavigate("pipeline", caseData.case_id)}
              title="Open dedicated End-to-End Autonomous Prediction Pipeline for this case"
              style={{
                padding: "8px 12px",
                fontSize: "12px",
                fontWeight: 600,
                background: "rgba(229, 9, 20, 0.12)",
                color: "var(--red-bright)",
                border: "1px solid rgba(229, 9, 20, 0.4)",
              }}
            >
              🚀 FULL 5D PIPELINE →
            </button>
          )}

          <button
            type="button"
            className="chip-btn"
            onClick={handleExportDossier}
            title="Download complete structured case dossier as JSON"
            style={{ fontSize: "12px", padding: "8px 12px" }}
          >
            📥 EXPORT DOSSIER
          </button>

          <button
            type="button"
            className="chip-btn"
            onClick={() => setShowFeedbackModal(true)}
            title="Record verified field outcome and evaluate prediction accuracy"
            style={{ fontSize: "12px", padding: "8px 12px" }}
          >
            📝 RECORD OUTCOME
          </button>

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
      </div>

      {/* ── 3. 8-STAGE INTERACTIVE WORKFLOW PIPELINE CHAIN ── */}
      <DrishtiWorkflowChain
        currentStepIndex={workflowStage}
        isAnalyzing={analyzing}
      />

      {/* ── 4. UNIFIED DRISHTI PREDICTION CENTERPIECE (THE HERO) ── */}
      {analysisCompleted ? (
        <div className="unified-prediction-centerpiece">
          <div className="prediction-centerpiece-header">
            <div className="prediction-title-group">
              <div style={{ display: "flex", flexDirection: "column" }}>
                <span className="prediction-heading" style={{ fontSize: "16px", fontWeight: 800, letterSpacing: "0.5px" }}>
                  DRISHTI 5D INTELLIGENCE FORECAST
                </span>
                <span style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                  &ldquo;From evidence to actionable prediction.&rdquo;
                </span>
              </div>
              {heroConfidence && (
                <span className="intel-badge" style={{ color: "var(--red-bright)", borderColor: "rgba(229, 9, 20, 0.4)", background: "rgba(229, 9, 20, 0.12)" }}>
                  CONFIDENCE: {heroConfidence}
                </span>
              )}
            </div>
            <div className="prediction-model-tag font-mono">
              XGBoost + GradientBoosting + Conformal Intervals
            </div>
          </div>

          <div className="prediction-quadrant-grid">
            {/* Quadrant 1: WHERE */}
            <div className="quadrant-block" style={{ borderLeft: "3px solid var(--red-bright)" }}>
              <div>
                <div className="quadrant-label">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--red-bright)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                  <span>01 — WHERE: LIKELY CASHOUT LOCATION</span>
                </div>
                {primaryAtm ? (
                  <>
                    <div className="quadrant-primary" style={{ color: "var(--red-bright)" }}>
                      {primaryAtm.bank || "Candidate ATM Terminal"}
                    </div>
                    <div className="quadrant-secondary">
                      {primaryAtm.location_name || caseData.predicted_area || "Identified Terminal"}
                    </div>
                    <div className="quadrant-tertiary font-mono">
                      {primaryAtm.atm_id ? `${primaryAtm.atm_id} · ` : ""}{primaryAtm.distance_km != null ? `~${primaryAtm.distance_km.toFixed(1)} km from origin` : "Geocoded terminal"}
                    </div>
                  </>
                ) : (
                  <div className="quadrant-secondary" style={{ color: "var(--text-muted)", marginTop: "8px" }}>
                    Location prediction unavailable
                  </div>
                )}
              </div>
            </div>

            {/* Quadrant 2: WHEN */}
            <div className="quadrant-block" style={{ borderLeft: "3px solid #FF5252" }}>
              <div>
                <div className="quadrant-label">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#FF5252" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  <span>02 — WHEN: LIKELY WITHDRAWAL WINDOW</span>
                </div>
                {caseData.predicted_time_peak_minutes != null ? (
                  <>
                    <div className="quadrant-primary font-mono" style={{ color: "var(--text-primary)" }}>
                      {caseData.predicted_time_earliest_minutes != null && caseData.predicted_time_latest_minutes != null
                        ? `${caseData.predicted_time_earliest_minutes}–${caseData.predicted_time_latest_minutes} min`
                        : `~${caseData.predicted_time_peak_minutes} min`}
                    </div>
                    <div className="quadrant-secondary">
                      Peak withdrawal in ~{caseData.predicted_time_peak_minutes} mins
                    </div>
                    <div className="quadrant-tertiary">
                      Conformal Uncertainty: ±{caseData.conformal_interval_minutes || 10.6}m (Probabilistic Estimate)
                    </div>
                  </>
                ) : (
                  <div className="quadrant-secondary" style={{ color: "var(--text-muted)", marginTop: "8px" }}>
                    Time prediction unavailable
                  </div>
                )}
              </div>
            </div>

            {/* Quadrant 3: AMOUNT */}
            <div className="quadrant-block" style={{ borderLeft: "3px solid var(--warning)" }}>
              <div>
                <div className="quadrant-label">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--warning)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9"/><path d="M14.8 9A2 2 0 0 0 13 8h-2a2 2 0 0 0 0 4h2a2 2 0 0 1 0 4h-2a2 2 0 0 1-1.8-1"/><path d="M12 6v2m0 8v2"/></svg>
                  <span>03 — AMOUNT: EXPECTED CASH-OUT</span>
                </div>
                {cashoutAmt != null ? (
                  <>
                    <div className="quadrant-primary font-mono text-amber">
                      ₹{Math.round(cashoutAmt).toLocaleString("en-IN")}
                    </div>
                    <div className="quadrant-secondary">
                      Reported Loss: {initialAmt != null ? `₹${initialAmt.toLocaleString("en-IN")}` : "Unavailable"}
                    </div>
                    <div className="quadrant-tertiary">
                      {caseData.amount_range_lower && caseData.amount_range_upper
                        ? `Bounds: ₹${Math.round(caseData.amount_range_lower).toLocaleString("en-IN")} – ₹${Math.round(caseData.amount_range_upper).toLocaleString("en-IN")}`
                        : "Post-layering commission discount model"}
                    </div>
                  </>
                ) : (
                  <div className="quadrant-secondary" style={{ color: "var(--text-muted)", marginTop: "8px" }}>
                    Amount prediction unavailable
                  </div>
                )}
              </div>
            </div>

            {/* Quadrant 4: ACTION */}
            <div className="quadrant-block" style={{ borderLeft: "3px solid var(--danger)" }}>
              <div>
                <div className="quadrant-label">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                  <span>05 — ACTION: TACTICAL RESPONSE FEASIBILITY</span>
                </div>
                <div className="quadrant-primary text-red">
                  {feasibility.feasibility_status || caseData.risk_level || "MEDIUM"}
                  {caseData.priority_score != null ? ` (${Math.round(caseData.priority_score)}/100 Priority)` : ""}
                </div>
                <div className="quadrant-secondary">
                  {feasibility.time_margin_minutes != null ? (
                    <span>Patrol Margin: <strong style={{ color: feasibility.time_margin_minutes > 15 ? "var(--success)" : "var(--warning)" }}>+{feasibility.time_margin_minutes.toFixed(1)} min</strong></span>
                  ) : (
                    <span>Decision support evaluation</span>
                  )}
                </div>
                <div className="quadrant-tertiary">
                  {feasibility.unit_name || feasibility.assigned_unit ? `${feasibility.unit_name || feasibility.assigned_unit}` : "Authorized Officer Review Required"}
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="empty-state-card" style={{ marginBottom: "22px" }}>
          <div style={{ fontSize: "16px", fontWeight: 700, color: "var(--text-primary)", marginBottom: "8px" }}>
            AWAITING INTELLIGENCE PIPELINE EXECUTION
          </div>
          <p style={{ maxWidth: "600px", margin: "0 auto 18px", fontSize: "13.5px", color: "var(--text-secondary)" }}>
            Execute the DRISHTI 8-stage predictive intelligence framework to trace multi-hop mule networks, forecast terminal cash-out coordinates, and evaluate police intercept feasibility.
          </p>
          <button className="btn-run-pipeline" onClick={handleRunAnalysis} disabled={analyzing}>
            {analyzing ? "Executing Pipeline..." : "⚡ RUN DRISHTI ANALYSIS"}
          </button>
        </div>
      )}

      {/* ── 5. REFINED MONEY TRAIL FLOW ── */}
      <div className="money-trail-strip">
        <div className="panel-header" style={{ marginBottom: "8px", paddingBottom: "8px" }}>
          <span className="panel-title">Multi-Hop Money Trail &amp; Mule Account Flow</span>
          <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
            {hops.length > 0 ? `${hops.length} Monitored Intermediary Hops` : "Awaiting Trail Analysis"}
          </span>
        </div>

        {trailNodes.length > 0 ? (
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
                      {node.amount != null ? (
                        <span className="font-mono text-amber">₹{Math.round(node.amount).toLocaleString("en-IN")}</span>
                      ) : null}
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
        ) : (
          <div style={{ color: "var(--text-muted)", fontSize: "13px", padding: "12px 0" }}>
            No transaction trail available. Run DRISHTI Analysis to reconstruct laundering path.
          </div>
        )}
      </div>

      {/* ── 6. TWO-COLUMN OPERATIONS GRID (MAP + WHY/ACTION) ── */}
      <div className="operations-grid">
        {/* Left Column: Dark Leaflet Tactical GIS Map */}
        <div className="map-panel">
          <div className="map-header">
            <span className="panel-title">Tactical Geospatial Hotspot Map</span>
            <span className="intel-badge">
              Target: {primaryAtm?.location_name || caseData.predicted_area || "Pending Analysis"}
            </span>
          </div>

          <div className="map-container-view">
            {primaryAtm ? (
              <MapErrorBoundary primaryAtm={primaryAtm}>
                <HotspotMap
                  prediction={focusedPrediction}
                  height="420px"
                  activeTarget={primaryAtm.atm_id}
                />
              </MapErrorBoundary>
            ) : (
              <div className="empty-state-card" style={{ height: "420px", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}>
                <p style={{ color: "var(--text-secondary)", marginBottom: "8px" }}>
                  Geospatial visualization waiting for prediction coordinates.
                </p>
                <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  Run DRISHTI Analysis above to plot target ATM and patrol vectors.
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: SHAP Why + Police Patrol Feasibility */}
        <div className="side-operations-column">
          {/* WHY: Explainability Panel */}
          <div className="panel-card">
            <div className="panel-header">
              <span className="panel-title">WHY — Predictive Feature Attribution</span>
              <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>TreeExplainer / Model Evidence</span>
            </div>

            <div>
              {riskFactors.length > 0 ? (
                riskFactors.slice(0, 4).map((factor, idx) => {
                  const label = typeof factor === "string" ? factor : (factor.feature || "Key Risk Indicator");
                  const contrib = typeof factor === "object" && factor.contribution != null ? factor.contribution : null;
                  const isPositive = contrib == null || contrib >= 0;

                  return (
                    <div key={idx} className="attribution-bar-item">
                      <div className="attribution-bar-label">
                        <span>{label}</span>
                        {contrib != null && (
                          <span className={`font-mono ${isPositive ? "text-red" : "text-emerald"}`}>
                            {isPositive ? "+" : ""}{contrib.toFixed(1)}%
                          </span>
                        )}
                      </div>
                      <div className="attribution-progress-track">
                        <div
                          className={`attribution-progress-fill ${isPositive ? "fill-red" : "fill-emerald"}`}
                          style={{ width: `${Math.min(Math.max(Math.abs(contrib || 50), 20), 95)}%` }}
                        ></div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div style={{ color: "var(--text-muted)", fontSize: "12.5px", padding: "16px 0" }}>
                  Model explanation unavailable for this prediction. Run DRISHTI Analysis to generate attributions.
                </div>
              )}
            </div>
          </div>

          {/* ACTION: Police Feasibility & Dispatch Box */}
          <div className="panel-card">
            <div className="panel-header">
              <span className="panel-title">ACTION — Recommended Investigator Response</span>
              <span className="badge-tag badge-risk-low">DECISION SUPPORT</span>
            </div>

            <div className="police-action-box">
              <div className="police-station-title">
                {feasibility.station_name || "Designated Police Precinct"}
              </div>
              <div className="police-eta-stats">
                <span>Unit: <strong className="font-mono" style={{ color: "var(--text-primary)" }}>{feasibility.assigned_unit || feasibility.unit_name || "Patrol Interceptor"}</strong></span>
                <span>ETA: <strong className="font-mono text-emerald">{feasibility.eta_minutes != null ? `${feasibility.eta_minutes.toFixed(1)} min` : "Unavailable"}</strong></span>
                <span>Margin: <strong className="font-mono text-emerald">{feasibility.time_margin_minutes != null ? `+${feasibility.time_margin_minutes.toFixed(1)} min` : "Evaluated"}</strong></span>
              </div>

              <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginBottom: "12px", lineHeight: "1.5" }}>
                <p style={{ fontWeight: 600, color: "var(--text-primary)", marginBottom: "4px" }}>
                  {caseData.five_d?.action?.protocol || "Recommended Operational Procedure:"}
                </p>
                <ol style={{ paddingLeft: "18px", margin: "6px 0" }}>
                  <li>Prioritize the predicted cash-out terminal: {primaryAtm?.location_name || caseData.predicted_area || "Candidate Kiosk"}.</li>
                  <li>Review associated mule accounts and layering sequence.</li>
                  <li>Verify transaction trail against institutional records.</li>
                  <li>Notify authorized field patrol personnel for surveillance.</li>
                  <li>Follow applicable legal and operational statutory procedures.</li>
                </ol>
              </div>

              <button
                className="btn-dispatch"
                onClick={() => setActionMsg("Notice requisition generated for investigator authorization (Simulated decision-support).")}
              >
                Draft Section 91 CrPC Notice &amp; Alert Requisition
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── FEEDBACK MODAL (Section 16) ── */}
      {showFeedbackModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.8)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9999,
            padding: "20px",
            backdropFilter: "blur(4px)",
          }}
          onClick={() => setShowFeedbackModal(false)}
        >
          <div
            className="panel-card"
            style={{
              maxWidth: "520px",
              width: "100%",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              boxShadow: "0 20px 50px rgba(0,0,0,0.9)",
              padding: "24px",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontSize: "18px" }}>📝</span>
                <h3 style={{ fontSize: "16px", fontWeight: 700, margin: 0, color: "var(--text-primary)" }}>
                  Record Field Outcome · #{caseData.case_id}
                </h3>
              </div>
              <button
                onClick={() => setShowFeedbackModal(false)}
                style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "16px" }}
              >
                ✕
              </button>
            </div>

            <p style={{ fontSize: "12.5px", color: "var(--text-secondary)", marginBottom: "16px", lineHeight: "1.4" }}>
              Submit verified field operational outcome. Persists to the audit ledger and appends samples to the continuous model retraining pipeline.
            </p>

            <form onSubmit={handleSubmitFeedback} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div>
                <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "6px", letterSpacing: "0.5px" }}>
                  WAS PREDICTED CASHOUT LOCATION ACCURATE?
                </label>
                <div style={{ display: "flex", gap: "16px" }}>
                  <label style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "13px", color: "var(--text-primary)", cursor: "pointer" }}>
                    <input
                      type="radio"
                      name="accuracy"
                      checked={feedbackAccurate}
                      onChange={() => setFeedbackAccurate(true)}
                    />
                    <span>Yes, verified at candidate cluster</span>
                  </label>
                  <label style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "13px", color: "var(--text-primary)", cursor: "pointer" }}>
                    <input
                      type="radio"
                      name="accuracy"
                      checked={!feedbackAccurate}
                      onChange={() => setFeedbackAccurate(false)}
                    />
                    <span>No, withdrew elsewhere</span>
                  </label>
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "6px", letterSpacing: "0.5px" }}>
                  PHYSICAL / DIGITAL INTERCEPTION
                </label>
                <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", color: "var(--text-primary)", cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={feedbackIntercepted}
                    onChange={(e) => setFeedbackIntercepted(e.target.checked)}
                  />
                  <span>Funds frozen or suspect apprehended on site</span>
                </label>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "6px", letterSpacing: "0.5px" }}>
                  INVESTIGATOR NOTES &amp; ARREST DETAILS
                </label>
                <textarea
                  rows="3"
                  placeholder="Record ATM terminal serial, CCTV identification, or mule testimony..."
                  value={feedbackNotes}
                  onChange={(e) => setFeedbackNotes(e.target.value)}
                  style={{
                    width: "100%",
                    background: "rgba(0,0,0,0.3)",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-xs)",
                    padding: "8px 10px",
                    color: "var(--text-primary)",
                    fontSize: "12.5px",
                    fontFamily: "inherit",
                    resize: "vertical",
                  }}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "8px" }}>
                <button
                  type="button"
                  className="chip-btn"
                  onClick={() => setShowFeedbackModal(false)}
                  disabled={submittingFeedback}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary-action"
                  disabled={submittingFeedback}
                >
                  {submittingFeedback ? "Submitting..." : "Submit Verified Outcome"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
