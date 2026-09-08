/**
 * src/components/AlertCard.jsx — Project DRISHTI
 * Ranked Alert Feed Card with Risk × Feasibility Priority Indicator,
 * 5D Intelligence Preview, and Deep-Dive Inspector Trigger.
 */

import { useState } from "react";
import OutcomeModal from "./OutcomeModal";

const FRAUD_LABEL = {
  upi_fraud: "UPI Fraud",
  kyc_fraud: "KYC Fraud",
  phishing:  "Phishing",
};

function formatINR(amount) {
  if (!amount && amount !== 0) return "—";
  return "Rs " + Math.round(Number(amount)).toLocaleString("en-IN");
}

export default function AlertCard({
  prediction,
  isSelected = false,
  isNew = false,
  onClick,
  onInspect,
  onFeedbackLogged,
}) {
  const [showModal, setShowModal] = useState(false);

  const {
    complaint_id,
    fraud_type,
    amount,
    alert_level,
    hotspot,
    time_window,
    five_d,
    top_k_locations,
    money_trail,
    feasibility,
    risk_score,
    risk_tier,
    processed_at,
  } = prediction;

  const timeStr = processed_at
    ? new Date(processed_at + "Z").toLocaleTimeString("en-IN", { hour12: false })
    : "—";

  const effectiveRiskTier = risk_tier || alert_level || "MEDIUM";
  const effectiveRiskScore = risk_score !== undefined ? Math.round(risk_score) : 65;

  // Composite Priority Score (Risk × Feasibility)
  const compositePriority = feasibility?.composite_priority
    ? Math.round(feasibility.composite_priority)
    : effectiveRiskScore;

  // Priority Rank Badge Label
  let priorityBadgeClass = "priority-p2";
  let priorityLabel = "P2 · ELEVATED INTERCEPT";
  if (compositePriority >= 75) {
    priorityBadgeClass = "priority-p1";
    priorityLabel = "P1 · CRITICAL INTERCEPT";
  } else if (compositePriority < 45) {
    priorityBadgeClass = "priority-p3";
    priorityLabel = "P3 · ROUTINE AUDIT";
  }

  const primaryATM = top_k_locations?.[0]?.location_name || hotspot?.location_name || "ATM Withdrawal Cluster";

  return (
    <>
      <div
        className={`alert-card ${effectiveRiskTier} ${isSelected ? "selected" : ""} ${isNew ? "new" : ""}`}
        onClick={() => onClick?.(prediction)}
        title="Click to select and center map"
      >
        {/* ── Top Row: Priority Badge & Risk Score ── */}
        <div className="alert-card-top">
          <span className={`priority-pill-badge ${priorityBadgeClass}`}>
            {priorityLabel} ({compositePriority}/100)
          </span>
          <span className="alert-card-time">{timeStr}</span>
        </div>

        {/* ── Second Row: Case ID & Fraud Category ── */}
        <div className="alert-card-id-row">
          <span className="alert-id">{complaint_id}</span>
          <span className={`fraud-badge fraud-${fraud_type}`}>
            {FRAUD_LABEL[fraud_type] || fraud_type}
          </span>
        </div>

        {/* ── Third Row: Financial Loss & Cash-Out Amount ── */}
        <div className="alert-card-financial-row">
          <div className="fin-col">
            <span className="fin-lbl">Reported Loss</span>
            <span className="fin-val text-red">{formatINR(amount)}</span>
          </div>
          <div className="fin-col">
            <span className="fin-lbl">Est. ATM Cash-Out</span>
            <span className="fin-val text-yellow">
              {formatINR(five_d?.amount?.estimated_cashout_amount || amount * 0.85)}
            </span>
          </div>
        </div>

        {/* ── Fourth Row: Predicted Hotspot & ETA Margin ── */}
        <div className="alert-card-hotspot-box">
          <div className="hotspot-pin-row">
            <span className="pin-icon">📍</span>
            <span className="hotspot-name" title={primaryATM}>
              {primaryATM}
            </span>
          </div>
          {feasibility && (
            <div className="hotspot-dispatch-row">
              <span className="van-icon">🚔</span>
              <span className="dispatch-text">
                {feasibility.unit_name} · ETA {feasibility.eta_minutes}m
              </span>
              <span className={`time-margin-tag status-${feasibility.feasibility_status}`}>
                {feasibility.time_margin_minutes > 0 ? `+${feasibility.time_margin_minutes}m` : `${feasibility.time_margin_minutes}m`}
              </span>
            </div>
          )}
        </div>

        {/* ── Fifth Row: Primary Action SOP Preview ── */}
        {five_d?.action?.primary_action && (
          <div className="alert-card-action-preview">
            <span className="action-sop-icon">⚡</span>
            <span className="action-sop-text">
              {five_d.action.primary_action}
            </span>
          </div>
        )}

        {/* ── Quick Card Actions ── */}
        <div className="alert-card-bottom-actions" onClick={e => e.stopPropagation()}>
          <button
            type="button"
            className="btn-inspect-5d"
            onClick={() => {
              onClick?.(prediction);
              onInspect?.(prediction);
            }}
          >
            🔍 Full 5D Dossier
          </button>

          <button
            type="button"
            className="btn-card-outcome"
            onClick={() => setShowModal(true)}
            title="Log physical interception outcome for active retraining"
          >
            ⚖️ Outcome
          </button>
        </div>
      </div>

      {/* Outcome Validation Modal */}
      {showModal && (
        <OutcomeModal
          prediction={prediction}
          onClose={() => setShowModal(false)}
          onFeedbackSubmitted={() => {
            onFeedbackLogged?.();
          }}
        />
      )}
    </>
  );
}
