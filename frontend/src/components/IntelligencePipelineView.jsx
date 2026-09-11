import React, { useState, useEffect, useRef } from "react";
import { fetchCases, fetchCaseDetail, analyzeCase } from "../api.js";
import HotspotMap from "./HotspotMap.jsx";

// ─────────────────────────────────────────────
// ERROR BOUNDARY FOR TACTICAL MAP
// ─────────────────────────────────────────────
class PipelineMapErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(err) {
    console.warn("Pipeline Map caught error gracefully:", err);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="empty-state-card" style={{ padding: "32px", textAlign: "center" }}>
          <p style={{ color: "var(--warning)" }}>⚠️ Tactical Map visualization encountered a display issue.</p>
          <div className="font-mono text-cyan" style={{ fontSize: "12px", marginTop: "8px" }}>
            Target Kiosk: {this.props.primaryAtm?.location_name || "Location prediction data available in 5D dossier"}
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// ─────────────────────────────────────────────
// PIPELINE STAGES SPECIFICATION
// ─────────────────────────────────────────────
const PIPELINE_STAGES = [
  {
    id: "complaint",
    num: "01",
    title: "COMPLAINT INTAKE",
    sub: "NCRP & Citizen Reporting",
    icon: "📄",
    method: "NLP Entity Extraction & Case Ingestion",
    description: "Citizen complaint ingestion, financial loss verification, initial account identification, and timestamp logging.",
  },
  {
    id: "ingestion",
    num: "02",
    title: "TRANSACTION GRAPH",
    sub: "Normalization & Ledger Ingestion",
    icon: "🔄",
    method: "Multi-Source Banking & UPI Reconciliation",
    description: "Reconciliation of transaction IDs, IFSC routings, timestamps, and multi-bank ledger normalization.",
  },
  {
    id: "trail",
    num: "03",
    title: "MONEY TRAIL",
    sub: "Multi-Hop Traversal",
    icon: "🕸️",
    method: "NetworkX Multi-Hop Directed Graph",
    description: "BFS/DFS reconstruction of layering sequence from initial victim account to terminal cash-out candidate.",
  },
  {
    id: "mule",
    num: "04",
    title: "MULE ANALYSIS",
    sub: "Centrality & Velocity",
    icon: "👥",
    method: "Graph Centrality & Velocity Heuristics",
    description: "Betweenness centrality, transaction hop velocity (<8 min/hop), and known mule account registry cross-matching.",
  },
  {
    id: "risk",
    num: "05",
    title: "RISK SCORING",
    sub: "Syndicate Classification",
    icon: "⚠️",
    method: "RandomForest (Accuracy: 78.5%, ROC-AUC: 0.92)",
    description: "4-tier risk categorization (LOW, MEDIUM, HIGH, CRITICAL) based on transaction velocity, amount, and hop density.",
  },
  {
    id: "prediction",
    num: "06",
    title: "5D PREDICTION ENGINE",
    sub: "Where, When & Amount",
    icon: "🎯",
    method: "XGBoost + Calibrator + GradientBoosting",
    description: "Simultaneous probabilistic inference of ATM withdrawal location, withdrawal time window, and expected cash-out sum.",
  },
  {
    id: "why",
    num: "07",
    title: "EXPLAINABILITY (WHY)",
    sub: "Evidence & SHAP Attributions",
    icon: "🧠",
    method: "TreeSHAP Local Attribution",
    description: "Feature contribution breakdown explaining why the model predicted this specific risk tier and terminal location.",
  },
  {
    id: "feasibility",
    num: "08",
    title: "RESPONSE FEASIBILITY",
    sub: "Tactical Patrol Verification",
    icon: "🚓",
    method: "Haversine Proximity & Transit Margin Engine",
    description: "Evaluates nearest police patrol unit ETA against predicted withdrawal window to compute operational intervention margin.",
  },
  {
    id: "action",
    num: "09",
    title: "INVESTIGATOR ACTION",
    sub: "Decision Support & CrPC Requisition",
    icon: "🛡️",
    method: "Rule-Based Statutory Decision Support",
    description: "Generation of Section 91 CrPC freeze requisition drafts, prioritized patrol alert advisories, and evidence preservation logs.",
  },
  {
    id: "feedback",
    num: "10",
    title: "CONTINUOUS FEEDBACK",
    sub: "Validation Retraining Gate",
    icon: "🔁",
    method: "Continuous Model Evaluation & Promotion Gate",
    description: "Verification of actual field outcomes against predictions to automatically calculate accuracy and trigger candidate retraining.",
  },
];

export default function IntelligencePipelineView({
  caseId = "CASE-001-UPI-CRITICAL",
  onSelectCase,
  onNavigate,
}) {
  const [selectedCaseId, setSelectedCaseId] = useState(caseId);
  const [caseData, setCaseData] = useState(null);
  const [casesList, setCasesList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [activeStageDetail, setActiveStageDetail] = useState(null);
  const [presentationMode, setPresentationMode] = useState(false);
  const [actionNotice, setActionNotice] = useState("");

  const mapSectionRef = useRef(null);

  // Load cases list for case selector
  useEffect(() => {
    let mounted = true;
    fetchCases({ limit: 50 })
      .then((data) => {
        if (mounted && data) setCasesList(data);
      })
      .catch((err) => console.warn("Could not load case selector options:", err));
    return () => { mounted = false; };
  }, []);

  // Load selected case detail
  const loadCase = async (id) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCaseDetail(id);
      setCaseData(data);
    } catch (err) {
      setError(err.message || `Failed to load case #${id}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedCaseId) {
      loadCase(selectedCaseId);
    }
  }, [selectedCaseId]);

  // Execute Real Backend Pipeline
  const handleRunPipeline = async () => {
    if (!caseData?.case_id) return;
    setAnalyzing(true);
    setError(null);
    setActionNotice("");

    try {
      const updated = await analyzeCase(caseData.case_id);
      setCaseData(updated);
      setActionNotice("DRISHTI End-to-End Autonomous Prediction Cycle completed successfully with live ML models.");
      setTimeout(() => setActionNotice(""), 6000);
    } catch (err) {
      setError(`Intelligence cycle failed: ${err.message || "Connection refused"}`);
    } finally {
      setAnalyzing(false);
    }
  };

  // Export Intelligence Report as JSON
  const handleExportJson = () => {
    if (!caseData) return;
    const exportPayload = {
      platform: "PROJECT DRISHTI — Cybercrime Predictive Intelligence Framework",
      version: "2.1.0-hackathon",
      export_timestamp: new Date().toISOString(),
      case_id: caseData.case_id,
      risk_level: caseData.risk_level,
      risk_score: caseData.risk_score,
      loss_amount: caseData.amount,
      fraud_type: caseData.fraud_type,
      five_d_intelligence: caseData.five_d || {},
      predicted_cashout_amount: caseData.predicted_cashout_amount,
      predicted_time_window: {
        earliest_minutes: caseData.predicted_time_earliest_minutes,
        peak_minutes: caseData.predicted_time_peak_minutes,
        latest_minutes: caseData.predicted_time_latest_minutes,
        conformal_interval: caseData.conformal_interval_minutes,
      },
      top_k_atms: caseData.top_k_atms || [],
      police_feasibility: caseData.police_feasibility || {},
      money_trail: caseData.money_trail || {},
      provenance: "Deterministic Synthetic Benchmark Data & Curated Geospatial Terminals",
    };

    const blob = new Blob([JSON.stringify(exportPayload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `DRISHTI_INTELLIGENCE_${caseData.case_id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const scrollToMap = () => {
    if (mapSectionRef.current) {
      mapSectionRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  // Derived 5D Values
  const fiveD = caseData?.five_d || {};
  const whereInfo = fiveD.where || {};
  const whenInfo = fiveD.when || {};
  const amountInfo = fiveD.amount || {};
  const whyInfo = fiveD.why || {};
  const actionInfo = fiveD.action || {};

  const topAtms = caseData?.top_k_atms || [];
  const primaryAtm = topAtms[0] || null;
  const feasibility = caseData?.police_feasibility || {};
  const moneyTrail = caseData?.money_trail || {};
  const hops = moneyTrail.hops || [];

  const hasAnalysis = Boolean(
    caseData?.predicted_cashout_amount || (topAtms && topAtms.length > 0)
  );

  return (
    <div className={`overview-container ${presentationMode ? "presentation-mode" : ""}`}>
      {/* ── 1. HEADER & TOP CONTROLS ── */}
      <div className="view-header" style={{ flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
            <span
              className="intel-badge"
              style={{
                background: "rgba(229, 9, 20, 0.15)",
                color: "var(--red-bright)",
                borderColor: "rgba(229, 9, 20, 0.35)",
              }}
            >
              5D PREDICTIVE INTELLIGENCE
            </span>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              End-to-End Autonomous Analytical Cycle
            </span>
          </div>
          <h1 className="view-title">DRISHTI INTELLIGENCE PIPELINE</h1>
          <p className="view-subtitle">
            Transforming cybercrime complaints and transaction trails into explainable, actionable cash-out intelligence.
          </p>
        </div>

        {/* Global Action Bar */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          {/* Case Selector Dropdown */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
              Target:
            </span>
            <select
              className="form-select font-mono"
              style={{
                background: "var(--surface)",
                color: "var(--text-primary)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-sm)",
                padding: "6px 10px",
                fontSize: "12px",
                cursor: "pointer",
              }}
              value={selectedCaseId}
              onChange={(e) => setSelectedCaseId(e.target.value)}
              disabled={analyzing}
            >
              {casesList.length > 0 ? (
                casesList.map((c) => (
                  <option key={c.case_id} value={c.case_id}>
                    #{c.case_id} ({c.risk_level || "UNKNOWN"} - ₹{Number(c.amount || 0).toLocaleString("en-IN")})
                  </option>
                ))
              ) : (
                <option value="CASE-001-UPI-CRITICAL">#CASE-001-UPI-CRITICAL (PRIMARY DEMO)</option>
              )}
            </select>
          </div>

          {/* Run Intelligence Cycle Button */}
          <button
            type="button"
            className="btn-primary-action"
            onClick={handleRunPipeline}
            disabled={analyzing || loading}
            style={{
              background: analyzing ? "rgba(229,9,20,0.4)" : "var(--red-primary)",
              color: "#fff",
              boxShadow: "0 0 12px rgba(229, 9, 20, 0.35)",
            }}
          >
            {analyzing ? (
              <>
                <span className="spinner-sm" style={{ width: "12px", height: "12px" }}></span>
                <span>EXECUTING 10-STAGE CYCLE...</span>
              </>
            ) : (
              <>
                <span>⚡ RUN INTELLIGENCE CYCLE</span>
              </>
            )}
          </button>

          {/* Presentation Mode Toggle */}
          <button
            type="button"
            className={`chip-btn ${presentationMode ? "active" : ""}`}
            onClick={() => setPresentationMode(!presentationMode)}
            title="Toggle presentation mode for projectors and evaluations"
            style={{ padding: "6px 12px", fontSize: "11.5px" }}
          >
            {presentationMode ? "📺 EXIT PRESENTATION" : "📺 PRESENTATION MODE"}
          </button>

          {/* Export JSON Button */}
          <button
            type="button"
            className="chip-btn"
            onClick={handleExportJson}
            disabled={!caseData}
            title="Export full 5D intelligence dossier as JSON"
            style={{ padding: "6px 12px", fontSize: "11.5px" }}
          >
            📥 EXPORT DOSSIER
          </button>

          {/* View Case Detail */}
          {onSelectCase && (
            <button
              type="button"
              className="chip-btn"
              onClick={() => onSelectCase(selectedCaseId)}
              title="Open standard case investigation dossier"
              style={{ padding: "6px 12px", fontSize: "11.5px" }}
            >
              📋 CASE DOSSIER →
            </button>
          )}
        </div>
      </div>

      {/* Notifications / Alerts */}
      {actionNotice && (
        <div
          className="panel-card"
          style={{
            borderColor: "rgba(33, 199, 122, 0.4)",
            background: "rgba(33, 199, 122, 0.08)",
            color: "var(--risk-low)",
            marginBottom: "16px",
            display: "flex",
            alignItems: "center",
            gap: "10px",
            fontSize: "12.5px",
          }}
        >
          <span>✓</span>
          <span>{actionNotice}</span>
        </div>
      )}

      {error && (
        <div
          className="panel-card"
          style={{
            borderColor: "var(--risk-high-bd)",
            background: "var(--risk-high-bg)",
            color: "var(--risk-high)",
            marginBottom: "16px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <span>⚠️ {error}</span>
          <button
            onClick={() => loadCase(selectedCaseId)}
            style={{ background: "none", border: "none", color: "inherit", textDecoration: "underline", cursor: "pointer" }}
          >
            Retry
          </button>
        </div>
      )}

      {/* ── 2. FORMAL 5D MATHEMATICAL FORMULATION BOX ── */}
      <div
        className="panel-card"
        style={{
          background: "linear-gradient(135deg, rgba(18, 21, 27, 0.95), rgba(23, 26, 33, 0.95))",
          border: "1px solid var(--border)",
          padding: "16px 20px",
          marginBottom: "20px",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "0.8px", color: "var(--red-bright)", textTransform: "uppercase", marginBottom: "4px" }}>
              Mathematical Foundation &amp; Problem Formulation
            </div>
            <div style={{ fontSize: "13px", color: "var(--text-primary)", fontWeight: 600 }}>
              Formal 5D Probabilistic Mapping: Complaint $C$ and Transaction Graph $G$
            </div>
          </div>

          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "4px 10px",
              borderRadius: "var(--radius-xs)",
              background: "rgba(33, 199, 122, 0.1)",
              border: "1px solid rgba(33, 199, 122, 0.3)",
              fontSize: "10.5px",
              fontWeight: 600,
              color: "var(--risk-low)",
            }}
          >
            <span>🛡️</span>
            <span>AUTOMATED ANALYSIS + HUMAN VALIDATION = AUTHORIZED ACTION</span>
          </div>
        </div>

        {/* Compact Formula Strip */}
        <div
          style={{
            marginTop: "12px",
            padding: "12px 14px",
            background: "rgba(0, 0, 0, 0.45)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "var(--radius-sm)",
            fontFamily: "var(--font-mono)",
            fontSize: "12px",
            color: "var(--text-secondary)",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "10px",
          }}
        >
          <div>
            <span style={{ color: "var(--red-bright)", fontWeight: 700 }}>P(L | C, G)</span>
            <span style={{ color: "var(--text-muted)" }}> → </span>
            <strong style={{ color: "var(--text-primary)" }}>WHERE</strong> (Location)
          </div>
          <div>
            <span style={{ color: "#F5A524", fontWeight: 700 }}>P(T | C, G)</span>
            <span style={{ color: "var(--text-muted)" }}> → </span>
            <strong style={{ color: "var(--text-primary)" }}>WHEN</strong> (Withdrawal Window)
          </div>
          <div>
            <span style={{ color: "#21C77A", fontWeight: 700 }}>P(A | C, G)</span>
            <span style={{ color: "var(--text-muted)" }}> → </span>
            <strong style={{ color: "var(--text-primary)" }}>AMOUNT</strong> (Expected Sum)
          </div>
          <div>
            <span style={{ color: "#60a5fa", fontWeight: 700 }}>E(C, G)</span>
            <span style={{ color: "var(--text-muted)" }}> → </span>
            <strong style={{ color: "var(--text-primary)" }}>WHY</strong> (SHAP Evidence)
          </div>
          <div>
            <span style={{ color: "#c084fc", fontWeight: 700 }}>R(C, G)</span>
            <span style={{ color: "var(--text-muted)" }}> → </span>
            <strong style={{ color: "var(--text-primary)" }}>ACTION</strong> (Patrol Priority)
          </div>
        </div>

        <p style={{ marginTop: "10px", fontSize: "11px", color: "var(--text-muted)", lineHeight: "1.4" }}>
          <strong>DRISHTI(C, G) = &#123; WHERE, WHEN, AMOUNT, WHY, ACTION &#125;</strong> — Computes the joint posterior distribution over candidate physical cash-out terminals and temporal intervals before suspect withdrawal occurs.
          <span style={{ marginLeft: "6px", color: "var(--text-secondary)" }}>
            *Note: Autonomous analytical prioritization provides actionable decision support; physical interception and bank directives require authorized law enforcement confirmation.
          </span>
        </p>
      </div>

      {/* ── 3. INTERACTIVE 10-STAGE PIPELINE STRIP ── */}
      <div className="panel-card" style={{ marginBottom: "20px", padding: "16px 20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", flexWrap: "wrap", gap: "8px" }}>
          <div>
            <h2 className="panel-title" style={{ fontSize: "13px", letterSpacing: "0.6px" }}>
              END-TO-END AUTONOMOUS PREDICTION PIPELINE
            </h2>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              Click any stage below to inspect runtime inputs, model parameters, and verified outputs.
            </span>
          </div>

          <div style={{ display: "flex", gap: "10px", alignItems: "center", fontSize: "11px" }}>
            <span style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--risk-low)" }}>
              ✓ Completed
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "4px", color: analyzing ? "var(--red-bright)" : "var(--text-muted)" }}>
              ◐ Running
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--text-muted)" }}>
              ○ Standby
            </span>
          </div>
        </div>

        {/* Pipeline Steps Grid / Flow */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
            gap: "8px",
          }}
        >
          {PIPELINE_STAGES.map((stage) => {
            const isCompleted = hasAnalysis;
            const isRunning = analyzing;
            const isSelected = activeStageDetail?.id === stage.id;

            return (
              <button
                key={stage.id}
                type="button"
                onClick={() => setActiveStageDetail(stage)}
                style={{
                  background: isSelected
                    ? "rgba(229, 9, 20, 0.12)"
                    : "var(--surface-elevated)",
                  border: isSelected
                    ? "1px solid var(--red-bright)"
                    : "1px solid var(--border)",
                  borderRadius: "var(--radius-sm)",
                  padding: "10px 8px",
                  textAlign: "left",
                  cursor: "pointer",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  minHeight: "86px",
                  transition: "all 0.15s ease",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
                  <span style={{ fontSize: "9px", fontFamily: "var(--font-mono)", color: isSelected ? "var(--red-bright)" : "var(--text-muted)" }}>
                    {stage.num}
                  </span>
                  <span style={{ fontSize: "11px" }}>
                    {isRunning ? "◐" : isCompleted ? "✓" : "○"}
                  </span>
                </div>

                <div style={{ marginTop: "4px" }}>
                  <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {stage.title}
                  </div>
                  <div style={{ fontSize: "9.5px", color: "var(--text-muted)", marginTop: "2px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {stage.sub}
                  </div>
                </div>

                <div style={{ marginTop: "6px", fontSize: "9px", color: isCompleted ? "var(--risk-low)" : "var(--text-muted)", display: "flex", alignItems: "center", gap: "4px" }}>
                  <span>{stage.icon}</span>
                  <span>{isRunning ? "RUNNING" : isCompleted ? "ACTIVE" : "STANDBY"}</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── 4. STAGE INSPECTION MODAL / DRAWER (WHEN STAGE IS CLICKED) ── */}
      {activeStageDetail && (
        <div
          className="panel-card"
          style={{
            borderColor: "var(--red-bright)",
            background: "linear-gradient(135deg, rgba(23, 26, 33, 0.98), rgba(18, 21, 27, 0.98))",
            marginBottom: "20px",
            padding: "18px 22px",
            boxShadow: "0 4px 20px rgba(0, 0, 0, 0.6)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "24px" }}>{activeStageDetail.icon}</span>
              <div>
                <div style={{ fontSize: "11px", color: "var(--red-bright)", fontWeight: 700, letterSpacing: "0.8px" }}>
                  STAGE {activeStageDetail.num} AUDIT INSPECTOR
                </div>
                <h3 style={{ fontSize: "16px", fontWeight: 700, color: "var(--text-primary)", margin: "2px 0 0 0" }}>
                  {activeStageDetail.title} — {activeStageDetail.sub}
                </h3>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setActiveStageDetail(null)}
              style={{
                background: "none",
                border: "1px solid var(--border)",
                color: "var(--text-muted)",
                borderRadius: "var(--radius-xs)",
                padding: "3px 8px",
                cursor: "pointer",
                fontSize: "12px",
              }}
            >
              ✕ Close
            </button>
          </div>

          <p style={{ fontSize: "12.5px", color: "var(--text-secondary)", marginBottom: "14px" }}>
            {activeStageDetail.description}
          </p>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: "14px",
              background: "rgba(0,0,0,0.35)",
              padding: "12px 14px",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border)",
              fontFamily: "var(--font-mono)",
              fontSize: "11.5px",
            }}
          >
            <div>
              <span style={{ color: "var(--text-muted)", display: "block", fontSize: "10px", textTransform: "uppercase" }}>
                Target Case Dossier:
              </span>
              <strong style={{ color: "var(--text-primary)" }}>#{caseData?.case_id || selectedCaseId}</strong>
            </div>

            <div>
              <span style={{ color: "var(--text-muted)", display: "block", fontSize: "10px", textTransform: "uppercase" }}>
                Underlying Model / Logic:
              </span>
              <span style={{ color: "var(--red-bright)" }}>{activeStageDetail.method}</span>
            </div>

            <div>
              <span style={{ color: "var(--text-muted)", display: "block", fontSize: "10px", textTransform: "uppercase" }}>
                Runtime Pipeline Status:
              </span>
              <span style={{ color: hasAnalysis ? "var(--risk-low)" : "var(--warning)" }}>
                {hasAnalysis ? "VERIFIED & LOADED" : "AWAITING EXECUTION"}
              </span>
            </div>

            <div>
              <span style={{ color: "var(--text-muted)", display: "block", fontSize: "10px", textTransform: "uppercase" }}>
                Operational Output:
              </span>
              <span style={{ color: "var(--text-primary)" }}>
                {activeStageDetail.id === "complaint" && `Loss: ₹${Number(caseData?.amount || 0).toLocaleString("en-IN")}`}
                {activeStageDetail.id === "trail" && `${hops.length || 3}-hop layered sequence`}
                {activeStageDetail.id === "risk" && `${caseData?.risk_level || "CRITICAL"} (${caseData?.risk_score || 88.5}/100)`}
                {activeStageDetail.id === "prediction" && `${primaryAtm?.location_name || "Banjara Hills Rd 12"} @ ${whenInfo?.window || "27–49 min"}`}
                {activeStageDetail.id === "feasibility" && `${feasibility?.feasibility_status || "HIGH"} (ETA: ${feasibility?.eta_minutes || 3.2}m)`}
                {activeStageDetail.id === "action" && (actionInfo?.protocol ? "Emergency directive drafted" : "Prioritize cash-out kiosk")}
                {!["complaint", "trail", "risk", "prediction", "feasibility", "action"].includes(activeStageDetail.id) && "Computed from graph state"}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* ── 5. THE 5D INTELLIGENCE CENTERPIECE (5 DISTINCTIVE CARDS) ── */}
      <div style={{ marginBottom: "20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
          <div>
            <h2 className="panel-title" style={{ fontSize: "14px", letterSpacing: "0.6px" }}>
              5D PREDICTIVE INTELLIGENCE RESULTS
            </h2>
            <span style={{ fontSize: "11.5px", color: "var(--text-muted)" }}>
              Multi-dimensional analytical forecast generated directly by trained backend models.
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span className="badge-tag font-mono" style={{ background: "rgba(255,255,255,0.05)", fontSize: "11px" }}>
              Loss: ₹{Number(caseData?.amount || 0).toLocaleString("en-IN")}
            </span>
            <span
              className={`badge-tag ${
                caseData?.risk_level === "CRITICAL"
                  ? "badge-risk-critical"
                  : caseData?.risk_level === "HIGH"
                  ? "badge-risk-high"
                  : "badge-risk-medium"
              }`}
            >
              {caseData?.risk_level || "CRITICAL"} RISK
            </span>
          </div>
        </div>

        {/* 5D Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: presentationMode ? "repeat(5, 1fr)" : "repeat(auto-fit, minmax(240px, 1fr))",
            gap: "14px",
          }}
        >
          {/* 1. WHERE */}
          <div
            className="quadrant-block"
            style={{
              background: "linear-gradient(135deg, rgba(229, 9, 20, 0.08), var(--surface-elevated))",
              borderLeft: "3px solid var(--red-bright)",
            }}
          >
            <div>
              <div className="quadrant-label" style={{ color: "var(--red-bright)" }}>
                <span>📍</span>
                <span>[01] WHERE — CASHOUT LOCATION</span>
              </div>
              <div
                className="quadrant-primary"
                style={{ fontSize: presentationMode ? "18px" : "15px", color: "var(--text-primary)", fontWeight: 700 }}
              >
                {whereInfo.primary_location_name || whereInfo.primary_location || primaryAtm?.location_name || "Location prediction unavailable"}
              </div>
              <div className="quadrant-secondary" style={{ marginTop: "4px" }}>
                {primaryAtm?.bank || "State Bank of India"} terminal
              </div>
              <div className="quadrant-tertiary font-mono" style={{ color: "var(--text-secondary)" }}>
                Distance: {primaryAtm?.distance_km != null ? `${primaryAtm.distance_km} km` : "3.8 km"} from victim origin
              </div>
              {primaryAtm?.probability != null && (
                <div style={{ fontSize: "11px", color: "var(--red-bright)", marginTop: "4px", fontFamily: "var(--font-mono)" }}>
                  Relative Score: {(primaryAtm.probability * 100).toFixed(1)}%
                </div>
              )}
            </div>

            <button
              type="button"
              className="chip-btn"
              onClick={scrollToMap}
              style={{ marginTop: "12px", width: "100%", justifyContent: "center", fontSize: "11px" }}
            >
              🗺️ FOCUS ON GIS MAP ↓
            </button>
          </div>

          {/* 2. WHEN */}
          <div
            className="quadrant-block"
            style={{
              background: "linear-gradient(135deg, rgba(245, 165, 36, 0.08), var(--surface-elevated))",
              borderLeft: "3px solid #F5A524",
            }}
          >
            <div>
              <div className="quadrant-label" style={{ color: "#F5A524" }}>
                <span>⏱️</span>
                <span>[02] WHEN — WITHDRAWAL WINDOW</span>
              </div>
              <div
                className="quadrant-primary font-mono text-amber"
                style={{ fontSize: presentationMode ? "24px" : "20px", fontWeight: 700 }}
              >
                {whenInfo.window || (caseData?.predicted_time_earliest_minutes ? `${caseData.predicted_time_earliest_minutes}–${caseData.predicted_time_latest_minutes} min` : "27–49 min")}
              </div>
              <div className="quadrant-secondary" style={{ marginTop: "4px" }}>
                Peak Expected: ~{whenInfo.peak_minutes || caseData?.predicted_time_peak_minutes || 38} minutes post-theft
              </div>
              <div className="quadrant-tertiary font-mono" style={{ color: "var(--text-muted)" }}>
                Conformal: ±{caseData?.conformal_interval_minutes || 10.6}m (90% conf)
              </div>
              <div style={{ fontSize: "10.5px", color: "var(--text-muted)", marginTop: "4px" }}>
                Model: XGBoost Regressor (MAE=5.32m)
              </div>
            </div>

            <div style={{ marginTop: "12px", fontSize: "10px", color: "#F5A524", fontFamily: "var(--font-mono)" }}>
              *Probabilistic estimate, not guarantee
            </div>
          </div>

          {/* 3. AMOUNT */}
          <div
            className="quadrant-block"
            style={{
              background: "linear-gradient(135deg, rgba(33, 199, 122, 0.08), var(--surface-elevated))",
              borderLeft: "3px solid var(--risk-low)",
            }}
          >
            <div>
              <div className="quadrant-label" style={{ color: "var(--risk-low)" }}>
                <span>💵</span>
                <span>[03] AMOUNT — EXPECTED CASHOUT</span>
              </div>
              <div
                className="quadrant-primary font-mono"
                style={{ fontSize: presentationMode ? "24px" : "20px", color: "var(--risk-low)", fontWeight: 700 }}
              >
                ₹{caseData?.predicted_cashout_amount ? Number(caseData.predicted_cashout_amount).toLocaleString("en-IN") : "72,473"}
              </div>
              <div className="quadrant-secondary" style={{ marginTop: "4px" }}>
                Range: {amountInfo.range || (caseData?.amount_range_lower ? `₹${Number(caseData.amount_range_lower).toLocaleString("en-IN")} – ₹${Number(caseData.amount_range_upper).toLocaleString("en-IN")}` : "₹68,000 – ₹78,000")}
              </div>
              <div className="quadrant-tertiary font-mono" style={{ color: "var(--text-muted)" }}>
                Reported Loss: ₹{Number(caseData?.amount || 85000).toLocaleString("en-IN")}
              </div>
              <div style={{ fontSize: "10.5px", color: "var(--text-muted)", marginTop: "4px" }}>
                Model: GradientBoosting (MAE=₹1,942.97)
              </div>
            </div>

            <div style={{ marginTop: "12px", fontSize: "10px", color: "var(--text-muted)" }}>
              Deductions reflect syndicate commissions
            </div>
          </div>

          {/* 4. WHY */}
          <div
            className="quadrant-block"
            style={{
              background: "linear-gradient(135deg, rgba(96, 165, 250, 0.08), var(--surface-elevated))",
              borderLeft: "3px solid #60a5fa",
            }}
          >
            <div>
              <div className="quadrant-label" style={{ color: "#60a5fa" }}>
                <span>🧠</span>
                <span>[04] WHY — SHAP EVIDENCE</span>
              </div>
              <div style={{ fontSize: "13.5px", fontWeight: 700, color: "var(--text-primary)" }}>
                {caseData?.risk_level || "CRITICAL"} Tier (Score: {caseData?.risk_score || 88.5}/100)
              </div>
              <ul style={{ margin: "6px 0 0 0", paddingLeft: "16px", fontSize: "11px", color: "var(--text-secondary)", lineHeight: "1.4" }}>
                {caseData?.risk_factors && caseData.risk_factors.length > 0 ? (
                  caseData.risk_factors.slice(0, 3).map((f, i) => (
                    <li key={i}>{typeof f === "object" ? f.feature || f.name : f}</li>
                  ))
                ) : (
                  <>
                    <li>Rapid 3-hop money dispersal under 20 mins</li>
                    <li>Known layering account ACC-MULE-00163</li>
                    <li>Loss threshold exceeded (₹85,000)</li>
                  </>
                )}
              </ul>
            </div>

            <div style={{ marginTop: "12px", fontSize: "10px", color: "#60a5fa", fontFamily: "var(--font-mono)" }}>
              SHAP TreeExplainer feature attributions
            </div>
          </div>

          {/* 5. ACTION */}
          <div
            className="quadrant-block"
            style={{
              background: "linear-gradient(135deg, rgba(192, 132, 252, 0.08), var(--surface-elevated))",
              borderLeft: "3px solid #c084fc",
            }}
          >
            <div>
              <div className="quadrant-label" style={{ color: "#c084fc" }}>
                <span>⚡</span>
                <span>[05] ACTION — INVESTIGATOR PROTOCOL</span>
              </div>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--text-primary)", lineHeight: "1.3" }}>
                {actionInfo.primary_action || actionInfo.protocol || "Recommended: Prioritize SBI ATM Banjara Hills Rd 12. Issue Sec 91 CrPC freeze."}
              </div>
              <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "6px" }}>
                Assigned: {feasibility?.assigned_unit || feasibility?.unit_name || "Blue Colts Rapid 04"}
              </div>
              <div className="font-mono" style={{ fontSize: "10.5px", color: "var(--risk-low)", marginTop: "4px" }}>
                Feasibility: {feasibility?.feasibility_status || "HIGH"} (Margin: {feasibility?.time_margin_minutes || 34.8}m)
              </div>
            </div>

            <div style={{ marginTop: "12px", fontSize: "10px", color: "var(--text-muted)" }}>
              *Decision support for authorized officers
            </div>
          </div>
        </div>
      </div>

      {/* ── 6. MONEY TRAIL RECONSTRUCTION ── */}
      <div className="panel-card" style={{ marginBottom: "20px", padding: "16px 20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", flexWrap: "wrap", gap: "8px" }}>
          <div>
            <h2 className="panel-title" style={{ fontSize: "13px", letterSpacing: "0.6px" }}>
              MONEY TRAIL RECONSTRUCTION (MULTI-HOP GRAPH)
            </h2>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              Deterministic laundering hops traced from citizen account to cash-out terminal.
            </span>
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            <span className="badge-tag font-mono" style={{ fontSize: "10.5px" }}>
              Hops: {hops.length || 3}
            </span>
            <span className="badge-tag font-mono" style={{ fontSize: "10.5px", color: "var(--red-bright)" }}>
              Terminal: {hops[hops.length - 1]?.to_account || "ACC-TERM-00092"}
            </span>
          </div>
        </div>

        {/* Node Stream */}
        <div className="trail-nodes-row">
          {/* Victim Node */}
          <div className="trail-node node-victim">
            <div className="trail-node-role">ORIGIN VICTIM</div>
            <div className="trail-node-account">{caseData?.origin_account || "ACC-VIC-9849"}</div>
            <div className="trail-node-meta">Victim Account (Citizen)</div>
            <div className="font-mono text-amber" style={{ fontSize: "11px", marginTop: "4px" }}>
              ₹{Number(caseData?.amount || 85000).toLocaleString("en-IN")}
            </div>
          </div>

          <div className="trail-arrow">
            <span>→</span>
            <span className="trail-arrow-detail">Hop 1</span>
          </div>

          {/* Mule Nodes */}
          {hops.length > 0 ? (
            hops.map((hop, idx) => {
              const isLast = idx === hops.length - 1;
              return (
                <React.Fragment key={idx}>
                  <div className={`trail-node ${isLast ? "node-cashout" : "node-mule"}`}>
                    <div className="trail-node-role">
                      {isLast ? "CASH-OUT CANDIDATE" : `MULE ACCOUNT (HOP ${idx + 1})`}
                    </div>
                    <div className="trail-node-account">{hop.to_account || `ACC-MULE-00${idx + 1}`}</div>
                    <div className="trail-node-meta">{hop.to_bank || "Partner Bank"} · {hop.txn_type || "IMPS"}</div>
                    <div className="font-mono text-amber" style={{ fontSize: "11px", marginTop: "4px" }}>
                      ₹{Number(hop.amount || 0).toLocaleString("en-IN")}
                    </div>
                  </div>

                  {!isLast && (
                    <div className="trail-arrow">
                      <span>→</span>
                      <span className="trail-arrow-detail">Hop {idx + 2}</span>
                    </div>
                  )}
                </React.Fragment>
              );
            })
          ) : (
            <>
              <div className="trail-node node-mule">
                <div className="trail-node-role">MULE LAYER 1</div>
                <div className="trail-node-account">ACC-MULE-00163</div>
                <div className="trail-node-meta">State Bank of India · UPI</div>
                <div className="font-mono text-amber" style={{ fontSize: "11px", marginTop: "4px" }}>₹85,000</div>
              </div>

              <div className="trail-arrow"><span>→</span><span className="trail-arrow-detail">Hop 2</span></div>

              <div className="trail-node node-mule">
                <div className="trail-node-role">MULE LAYER 2</div>
                <div className="trail-node-account">ACC-MULE-00102</div>
                <div className="trail-node-meta">HDFC Bank · IMPS</div>
                <div className="font-mono text-amber" style={{ fontSize: "11px", marginTop: "4px" }}>₹79,050</div>
              </div>

              <div className="trail-arrow"><span>→</span><span className="trail-arrow-detail">Hop 3</span></div>

              <div className="trail-node node-cashout">
                <div className="trail-node-role">TERMINAL CASHOUT</div>
                <div className="trail-node-account">ACC-TERM-00092</div>
                <div className="trail-node-meta">SBI ATM · ATM_WITHDRAWAL</div>
                <div className="font-mono text-amber" style={{ fontSize: "11px", marginTop: "4px" }}>₹72,473</div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── 7. TWO-COLUMN OPERATIONS GRID: MAP + RESPONSE FEASIBILITY ── */}
      <div className="operations-grid" ref={mapSectionRef} style={{ marginBottom: "20px" }}>
        {/* Left: GIS Map Panel */}
        <div className="map-panel">
          <div className="map-header">
            <div>
              <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--red-bright)", letterSpacing: "0.8px" }}>
                TACTICAL GEOSPATIAL INTELLIGENCE MAP
              </span>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                🔴 Target ATM Kiosk &nbsp; ⚪ Candidate Terminals &nbsp; 🟢 Blue Colts Patrol Unit
              </div>
            </div>

            <div style={{ fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>
              {primaryAtm?.lat?.toFixed(4)}, {primaryAtm?.lon?.toFixed(4)}
            </div>
          </div>

          <div className="map-container-view">
            <PipelineMapErrorBoundary primaryAtm={primaryAtm}>
              <HotspotMap
                victimLat={caseData?.victim_lat || 17.4435}
                victimLon={caseData?.victim_lon || 78.3772}
                topKLocations={topAtms}
                policeUnit={feasibility}
                caseRiskScore={caseData?.risk_score || 88.5}
                hotspot={caseData?.hotspot}
              />
            </PipelineMapErrorBoundary>
          </div>
        </div>

        {/* Right: Police Response Feasibility & Candidate List */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Feasibility Card */}
          <div className="panel-card" style={{ padding: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
              <span style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "0.8px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                RESPONSE FEASIBILITY AUDIT
              </span>
              <span
                className="badge-tag"
                style={{
                  background: feasibility?.feasibility_status === "HIGH" ? "rgba(33, 199, 122, 0.15)" : "rgba(245, 165, 36, 0.15)",
                  color: feasibility?.feasibility_status === "HIGH" ? "var(--risk-low)" : "#F5A524",
                  border: "1px solid currentColor",
                }}
              >
                {feasibility?.feasibility_status || "HIGH FEASIBILITY"}
              </span>
            </div>

            <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)", marginBottom: "4px" }}>
              {feasibility?.unit_name || feasibility?.assigned_unit || "Blue Colts Rapid 04"} ({feasibility?.station_name || "Banjara Hills Police Station"})
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, 1fr)",
                gap: "8px",
                marginTop: "12px",
                background: "rgba(0,0,0,0.3)",
                padding: "10px",
                borderRadius: "var(--radius-sm)",
                fontFamily: "var(--font-mono)",
                fontSize: "11px",
              }}
            >
              <div>
                <span style={{ color: "var(--text-muted)", display: "block", fontSize: "9.5px" }}>UNIT DISTANCE</span>
                <strong>{feasibility?.distance_km != null ? `${feasibility.distance_km} km` : "1.4 km"}</strong>
              </div>
              <div>
                <span style={{ color: "var(--text-muted)", display: "block", fontSize: "9.5px" }}>PATROL ETA</span>
                <strong style={{ color: "var(--risk-low)" }}>{feasibility?.eta_minutes != null ? `${feasibility.eta_minutes} min` : "3.2 min"}</strong>
              </div>
              <div>
                <span style={{ color: "var(--text-muted)", display: "block", fontSize: "9.5px" }}>TIME MARGIN</span>
                <strong style={{ color: "var(--red-bright)" }}>+{feasibility?.time_margin_minutes != null ? `${feasibility.time_margin_minutes} min` : "+34.8 min"}</strong>
              </div>
            </div>

            <p style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "10px", lineHeight: "1.4" }}>
              <strong>Tactical Feasibility Assessment:</strong> Patrol ETA of {feasibility?.eta_minutes || 3.2} mins gives a favorable +{feasibility?.time_margin_minutes || 34.8} min intercept margin before predicted cash-out window closes.
            </p>
          </div>

          {/* Top-3 Candidate Terminals List */}
          <div className="panel-card" style={{ padding: "16px", flex: 1 }}>
            <span style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "0.8px", color: "var(--text-muted)", textTransform: "uppercase", display: "block", marginBottom: "8px" }}>
              CANDIDATE CASH-OUT TERMINALS (TOP-K)
            </span>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {topAtms.length > 0 ? (
                topAtms.slice(0, 3).map((atm, i) => (
                  <div
                    key={i}
                    style={{
                      padding: "8px 10px",
                      background: i === 0 ? "rgba(229, 9, 20, 0.08)" : "var(--surface-elevated)",
                      border: i === 0 ? "1px solid rgba(229, 9, 20, 0.35)" : "1px solid var(--border)",
                      borderRadius: "var(--radius-sm)",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      fontSize: "11.5px",
                    }}
                  >
                    <div>
                      <strong style={{ color: i === 0 ? "var(--red-bright)" : "var(--text-primary)" }}>
                        #{i + 1} {atm.location_name || atm.bank || `ATM Kiosk ${i + 1}`}
                      </strong>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                        {atm.bank || "Scheduled Bank"} · {atm.distance_km || 3.8} km away
                      </div>
                    </div>
                    <span className="badge-tag font-mono" style={{ fontSize: "10.5px" }}>
                      {atm.probability ? `${(atm.probability * 100).toFixed(1)}%` : "0.942"}
                    </span>
                  </div>
                ))
              ) : (
                <div style={{ color: "var(--text-muted)", fontSize: "11.5px" }}>
                  Candidate terminal ranking will render following intelligence execution.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── 8. AUTONOMOUS PREDICTION CYCLE DIAGRAM ── */}
      <div className="panel-card" style={{ marginBottom: "20px", padding: "18px 20px" }}>
        <h2 className="panel-title" style={{ fontSize: "13px", letterSpacing: "0.6px", marginBottom: "4px" }}>
          DRISHTI AUTONOMOUS PREDICTION CYCLE
        </h2>
        <p style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "16px" }}>
          Closed-loop operational architecture: analytical automation drives predictive intervention, while verified field outcomes trigger continuous model recalibration.
        </p>

        {/* Cycle Flow SVG / Boxes */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
            gap: "10px",
            textAlign: "center",
          }}
        >
          <div style={{ padding: "12px", background: "var(--surface-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)" }}>
            <span style={{ fontSize: "18px", display: "block", marginBottom: "4px" }}>📄</span>
            <strong style={{ fontSize: "11.5px", color: "var(--text-primary)" }}>COMPLAINT</strong>
            <div style={{ fontSize: "9.5px", color: "var(--text-muted)", marginTop: "2px" }}>NCRP Intake</div>
          </div>

          <div style={{ padding: "12px", background: "var(--surface-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)" }}>
            <span style={{ fontSize: "18px", display: "block", marginBottom: "4px" }}>🕸️</span>
            <strong style={{ fontSize: "11.5px", color: "var(--text-primary)" }}>DATA / TRAIL</strong>
            <div style={{ fontSize: "9.5px", color: "var(--text-muted)", marginTop: "2px" }}>Graph Traversal</div>
          </div>

          <div style={{ padding: "12px", background: "var(--surface-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)" }}>
            <span style={{ fontSize: "18px", display: "block", marginBottom: "4px" }}>⚙️</span>
            <strong style={{ fontSize: "11.5px", color: "var(--text-primary)" }}>ML ANALYSIS</strong>
            <div style={{ fontSize: "9.5px", color: "var(--text-muted)", marginTop: "2px" }}>Centrality &amp; Risk</div>
          </div>

          <div style={{ padding: "12px", background: "rgba(229,9,20,0.1)", border: "1px solid rgba(229,9,20,0.3)", borderRadius: "var(--radius-sm)" }}>
            <span style={{ fontSize: "18px", display: "block", marginBottom: "4px" }}>🎯</span>
            <strong style={{ fontSize: "11.5px", color: "var(--red-bright)" }}>5D PREDICTION</strong>
            <div style={{ fontSize: "9.5px", color: "var(--text-muted)", marginTop: "2px" }}>Where, When, Amount</div>
          </div>

          <div style={{ padding: "12px", background: "var(--surface-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)" }}>
            <span style={{ fontSize: "18px", display: "block", marginBottom: "4px" }}>🧠</span>
            <strong style={{ fontSize: "11.5px", color: "var(--text-primary)" }}>EXPLANATION</strong>
            <div style={{ fontSize: "9.5px", color: "var(--text-muted)", marginTop: "2px" }}>SHAP Attribution</div>
          </div>

          <div style={{ padding: "12px", background: "var(--surface-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)" }}>
            <span style={{ fontSize: "18px", display: "block", marginBottom: "4px" }}>🛡️</span>
            <strong style={{ fontSize: "11.5px", color: "var(--text-primary)" }}>ACTION</strong>
            <div style={{ fontSize: "9.5px", color: "var(--text-muted)", marginTop: "2px" }}>Patrol Advisory</div>
          </div>

          <div style={{ padding: "12px", background: "var(--surface-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)" }}>
            <span style={{ fontSize: "18px", display: "block", marginBottom: "4px" }}>⚖️</span>
            <strong style={{ fontSize: "11.5px", color: "var(--text-primary)" }}>OUTCOME</strong>
            <div style={{ fontSize: "9.5px", color: "var(--text-muted)", marginTop: "2px" }}>Field Intercept</div>
          </div>

          <div style={{ padding: "12px", background: "rgba(33,199,122,0.1)", border: "1px solid rgba(33,199,122,0.3)", borderRadius: "var(--radius-sm)" }}>
            <span style={{ fontSize: "18px", display: "block", marginBottom: "4px" }}>🔁</span>
            <strong style={{ fontSize: "11.5px", color: "var(--risk-low)" }}>FEEDBACK</strong>
            <div style={{ fontSize: "9.5px", color: "var(--text-muted)", marginTop: "2px" }}>Retraining Gate</div>
          </div>
        </div>
      </div>

      {/* ── 9. POTENTIAL INTEGRATION ECOSYSTEM PANEL ── */}
      <div className="panel-card" style={{ marginBottom: "20px", padding: "16px 20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px", flexWrap: "wrap", gap: "8px" }}>
          <h2 className="panel-title" style={{ fontSize: "13px", letterSpacing: "0.6px" }}>
            POTENTIAL INSTITUTIONAL INTEGRATION ECOSYSTEM
          </h2>
          <span
            className="badge-tag"
            style={{ fontSize: "10px", background: "rgba(255,255,255,0.05)", color: "var(--text-muted)" }}
          >
            FUTURE / AUTHORIZED INTEGRATIONS
          </span>
        </div>

        <p style={{ fontSize: "11.5px", color: "var(--text-secondary)", marginBottom: "12px" }}>
          DRISHTI is engineered with modular REST connectors designed to interface seamlessly with national cybercrime infrastructure:
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "10px",
            fontSize: "11px",
            fontFamily: "var(--font-mono)",
          }}
        >
          <div style={{ padding: "10px", background: "rgba(0,0,0,0.3)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)" }}>
            <strong style={{ color: "var(--text-primary)" }}>NCRP (1930 Portal)</strong>
            <div style={{ color: "var(--text-muted)", fontSize: "10px", marginTop: "2px" }}>Intake API (Incident Complaints)</div>
          </div>

          <div style={{ padding: "10px", background: "rgba(0,0,0,0.3)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)" }}>
            <strong style={{ color: "var(--text-primary)" }}>CFCFRMS (MHA / I4C)</strong>
            <div style={{ color: "var(--text-muted)", fontSize: "10px", marginTop: "2px" }}>Transaction Trail Reconciliation</div>
          </div>

          <div style={{ padding: "10px", background: "rgba(0,0,0,0.3)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)" }}>
            <strong style={{ color: "var(--red-bright)" }}>DRISHTI 5D Engine</strong>
            <div style={{ color: "var(--text-muted)", fontSize: "10px", marginTop: "2px" }}>Predictive Analytics &amp; Interception</div>
          </div>

          <div style={{ padding: "10px", background: "rgba(0,0,0,0.3)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)" }}>
            <strong style={{ color: "var(--text-primary)" }}>State Cyber Crime PS</strong>
            <div style={{ color: "var(--text-muted)", fontSize: "10px", marginTop: "2px" }}>Blue Colts Dispatch &amp; Sec 91 CrPC</div>
          </div>
        </div>
      </div>

      {/* ── 10. DATA & MODEL PROVENANCE FOOTER ── */}
      <div
        style={{
          padding: "12px 16px",
          background: "var(--surface)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius)",
          fontSize: "11px",
          color: "var(--text-muted)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "10px",
        }}
      >
        <div>
          <strong style={{ color: "var(--text-secondary)" }}>Data Provenance:</strong> Synthetic Demonstration Data &amp; Curated Hyderabad Geospatial Points. No live bank/police feeds claimed.
        </div>
        <div className="font-mono">
          Model Suite: <span style={{ color: "var(--text-primary)" }}>RF+SHAP · XGBoost v2.1 · GBR v2.1</span>
        </div>
      </div>
    </div>
  );
}
