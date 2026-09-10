import React from "react";

/**
 * DrishtiWorkflowChain.jsx — 8-Stage Cybercrime Intelligence Pipeline
 *
 * Horizontal interactive workflow visualizer:
 * [01] COMPLAINT → [02] MONEY TRAIL → [03] MULE → [04] RISK → [05] PREDICTION → [06] MAP → [07] WHY → [08] ACTION
 */

function ComplaintIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  );
}

function TrailIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="18" cy="5" r="3" />
      <circle cx="6" cy="12" r="3" />
      <circle cx="18" cy="19" r="3" />
      <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
      <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
    </svg>
  );
}

function MuleIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="8.5" cy="7" r="4" />
      <line x1="18" y1="8" x2="23" y2="13" />
      <line x1="23" y1="8" x2="18" y2="13" />
    </svg>
  );
}

function RiskIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );
}

function PredictionIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="22" y1="12" x2="18" y2="12" />
      <line x1="6" y1="12" x2="2" y2="12" />
      <line x1="12" y1="6" x2="12" y2="2" />
      <line x1="12" y1="22" x2="12" y2="18" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function MapPinIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
      <circle cx="12" cy="10" r="3" />
    </svg>
  );
}

function WhyIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-2.04" />
      <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-2.04" />
    </svg>
  );
}

function ActionIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 11 12 14 22 4" />
      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
    </svg>
  );
}

export const WORKFLOW_STAGES = [
  { id: "complaint", num: "01", label: "COMPLAINT", icon: <ComplaintIcon />, desc: "NCRP intake & entity parsing" },
  { id: "money_trail", num: "02", label: "MONEY TRAIL", icon: <TrailIcon />, desc: "Multi-hop graph traversal" },
  { id: "mule", num: "03", label: "MULE", icon: <MuleIcon />, desc: "Layering & mule centrality" },
  { id: "risk", num: "04", label: "RISK", icon: <RiskIcon />, desc: "RandomForest classification" },
  { id: "prediction", num: "05", label: "PREDICTION", icon: <PredictionIcon />, desc: "Where, When & Amount regression" },
  { id: "map", num: "06", label: "MAP", icon: <MapPinIcon />, desc: "Geospatial cluster calibration" },
  { id: "why", num: "07", label: "WHY", icon: <WhyIcon />, desc: "SHAP feature attribution" },
  { id: "action", num: "08", label: "ACTION", icon: <ActionIcon />, desc: "Patrol intercept & Sec 91 CrPC" },
];

export default function DrishtiWorkflowChain({
  currentStepIndex = 8,
  isAnalyzing = false,
  className = "",
}) {
  return (
    <div className={`workflow-chain-wrapper ${className}`}>
      <div className="workflow-chain-header">
        <div className="workflow-chain-title">
          <span className="workflow-pulse-tag">DRISHTI INTELLIGENCE PIPELINE</span>
          <span className="workflow-chain-subtitle">End-to-End Autonomous Prediction Cycle</span>
        </div>
        <div className="workflow-status-indicator">
          {isAnalyzing ? (
            <span className="workflow-status-badge active font-mono">
              <span className="workflow-dot-pulse"></span> EXECUTING STAGE {currentStepIndex + 1}/8
            </span>
          ) : currentStepIndex >= 7 ? (
            <span className="workflow-status-badge complete font-mono">
              ✓ ANALYSIS COMPLETE · ALL 8 STAGES VERIFIED
            </span>
          ) : (
            <span className="workflow-status-badge pending font-mono">
              STANDBY · AWAITING INGESTION
            </span>
          )}
        </div>
      </div>

      <div className="workflow-chain-track">
        {WORKFLOW_STAGES.map((stage, idx) => {
          const isDone = isAnalyzing ? idx < currentStepIndex : currentStepIndex >= 7;
          const isCurrent = isAnalyzing && idx === currentStepIndex;
          const isPending = !isDone && !isCurrent;

          const stateClass = isCurrent
            ? "state-current"
            : isDone
            ? "state-completed"
            : "state-pending";

          return (
            <React.Fragment key={stage.id}>
              <div
                className={`workflow-node ${stateClass}`}
                title={`${stage.num} ${stage.label}: ${stage.desc}`}
              >
                <div className="workflow-node-top">
                  <span className="workflow-node-num">{stage.num}</span>
                  <span className="workflow-node-icon">{stage.icon}</span>
                </div>
                <div className="workflow-node-label">{stage.label}</div>
                <div className="workflow-node-state">
                  {isCurrent ? (
                    <span className="state-pill state-pill-current">Active ●</span>
                  ) : isDone ? (
                    <span className="state-pill state-pill-done">✓ Done</span>
                  ) : (
                    <span className="state-pill state-pill-pending">○ Ready</span>
                  )}
                </div>
              </div>

              {idx < WORKFLOW_STAGES.length - 1 && (
                <div className={`workflow-connector ${isDone ? "connector-done" : ""}`}>
                  <span className="connector-arrow">→</span>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
