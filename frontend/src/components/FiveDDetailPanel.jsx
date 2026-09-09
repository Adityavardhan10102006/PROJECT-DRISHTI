/**
 * src/components/FiveDDetailPanel.jsx — Project DRISHTI
 * Complete 5D Cybercrime Intelligence & Tactical Command Dossier.
 *
 * Visualizes the 5 Dimensions:
 *   1. WHERE  — Hotspot Coordinates, Cluster Density, Search Radius
 *   2. WHEN   — XGBoost Window, Peak Minutes, Tactical Time Margin
 *   3. AMOUNT — Reported Loss, Laundered Skimming, Cash-Out At Risk
 *   4. WHY    — AI Rationale, Factor Attributions (SHAP explainability)
 *   5. ACTION — Tactical Unit Assignment, Vehicle Callsign, SOP Directives
 */

import { useState } from "react";
import MoneyTrailFlow from "./MoneyTrailFlow";
import TopKLocationsPanel from "./TopKLocationsPanel";

function formatINR(val) {
  if (val === undefined || val === null) return "—";
  return "Rs " + Math.round(Number(val)).toLocaleString("en-IN");
}

export default function FiveDDetailPanel({
  prediction,
  onOpenOutcomeModal,
  onSelectLocation,
  onBackToList,
}) {
  const [activeSubTab, setActiveSubTab] = useState("dossier"); // "dossier" | "trail" | "topk"
  const [copied, setCopied] = useState(false);

  if (!prediction) {
    return (
      <div className="empty-dossier-state">
        <div className="radar-scanner">
          <div className="radar-sweep"></div>
        </div>
        <div className="empty-title">Tactical Operations Console</div>
        <div className="empty-desc">
          Select an active cybercrime alert or submit a complaint to generate full 5D predictive intelligence.
        </div>
      </div>
    );
  }

  const {
    complaint_id,
    fraud_type,
    amount,
    five_d = {},
    top_k_locations = [],
    money_trail,
    feasibility,
    risk_score = 65,
    risk_tier = "MEDIUM",
    processed_at,
    nlp_entities = {},
  } = prediction;

  const where  = five_d.where  || {};
  const when   = five_d.when   || {};
  const amt    = five_d.amount || {};
  const why    = five_d.why    || {};
  const action = five_d.action || {};

  const timeStr = processed_at
    ? new Date(processed_at + "Z").toLocaleTimeString("en-IN", { hour12: false })
    : "—";

  function handleCopyDispatch() {
    const text = `[DRISHTI TACTICAL DISPATCH]\nCase: ${complaint_id}\nType: ${fraud_type.toUpperCase()}\nLoss: Rs ${amount}\nRisk Score: ${Math.round(risk_score)}/100 (${risk_tier})\nTarget: ${where.primary_hotspot_name || "ATM Cluster"}\nETA: ${feasibility?.eta_minutes || 15}m | Window: ${when.peak_minutes || 35}m\nUnit: ${action.dispatch_unit || "Beat Patrol"}\nSOP: ${action.primary_action || "Dispatch interceptor"}`;
    navigator.clipboard?.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="dossier-container">
      {/* ── Dossier Header ── */}
      <div className="dossier-header">
        <div className="dossier-header-top">
          {onBackToList && (
            <button className="dossier-back-btn" onClick={onBackToList} title="Back to Alert Queue">
              ← Queue
            </button>
          )}
          <div className="dossier-id-group">
            <span className="dossier-id">{complaint_id}</span>
            <span className={`risk-tag-badge risk-${risk_tier.toLowerCase()}`}>
              {risk_tier} RISK ({Math.round(risk_score)}/100)
            </span>
            <span className="fraud-tag-badge">{fraud_type?.replace("_", " ").toUpperCase()}</span>
          </div>
          <span className="dossier-time">{timeStr}</span>
        </div>

        {/* Tactical Feasibility Strip */}
        {feasibility && (
          <div className="tactical-feasibility-strip">
            <div className="unit-info">
              <span className="unit-icon">🚔</span>
              <div>
                <span className="unit-name">{feasibility.unit_name}</span>
                <span className="unit-vehicle">({feasibility.unit_vehicle})</span>
              </div>
            </div>
            <div className="feasibility-metrics">
              <span className="eta-badge">ETA: {feasibility.eta_minutes}m</span>
              <span className={`margin-badge status-${feasibility.feasibility_status}`}>
                Margin: {feasibility.time_margin_minutes > 0 ? `+${feasibility.time_margin_minutes}m` : `${feasibility.time_margin_minutes}m`}
              </span>
            </div>
          </div>
        )}

        {/* Sub Navigation Bar */}
        <div className="dossier-nav-tabs">
          <button
            className={`dossier-tab-btn ${activeSubTab === "dossier" ? "active" : ""}`}
            onClick={() => setActiveSubTab("dossier")}
          >
            5D Dimensions
          </button>
          <button
            className={`dossier-tab-btn ${activeSubTab === "trail" ? "active" : ""}`}
            onClick={() => setActiveSubTab("trail")}
          >
            Money Trail ({money_trail?.hops?.length || 0})
          </button>
          <button
            className={`dossier-tab-btn ${activeSubTab === "topk" ? "active" : ""}`}
            onClick={() => setActiveSubTab("topk")}
          >
            Top-K ATMs ({top_k_locations.length})
          </button>
        </div>
      </div>

      {/* ── SubTab 1: 5D Intelligence Dimensions ── */}
      {activeSubTab === "dossier" && (
        <div className="dossier-scroll-body">
          {/* ACTION SECTION (Primary Priority) */}
          <div className="five-d-box box-action">
            <div className="box-header">
              <span className="box-dim-tag tag-action">5. ACTION (POLICE SOP)</span>
              <span className="box-urgency">{action.urgency_badge || "IMMEDIATE"}</span>
            </div>
            <div className="sop-primary-highlight">
              {action.primary_action || "Deploy nearest patrol unit to intercept criminal at predicted withdrawal ATM cluster."}
            </div>
            {action.secondary_actions?.length > 0 && (
              <ul className="sop-steps-list">
                {action.secondary_actions.map((act, i) => (
                  <li key={i} className="sop-step-item">
                    <span className="step-bullet">{i + 1}</span>
                    <span>{act}</span>
                  </li>
                ))}
              </ul>
            )}
            {action.relevant_statute && (
              <div className="statute-note">
                Legal Basis: <strong>{action.relevant_statute}</strong>
              </div>
            )}
          </div>

          {/* WHERE SECTION */}
          <div className="five-d-box box-where">
            <div className="box-header">
              <span className="box-dim-tag tag-where">1. WHERE (SPATIAL HOTSPOT)</span>
              <span className="box-meta-note">DBSCAN Density Cluster</span>
            </div>
            <div className="hotspot-main-name">
              {where.primary_hotspot_name || "ATM Withdrawal Cluster"}
            </div>
            <div className="where-metrics-grid">
              <div className="where-item">
                <span className="w-lbl">Perimeter Radius</span>
                <span className="w-val">{(where.radius_km || 0.6).toFixed(2)} km</span>
              </div>
              <div className="where-item">
                <span className="w-lbl">ATMs in Cluster</span>
                <span className="w-val">{where.cluster_atm_count || 3} active</span>
              </div>
              <div className="where-item">
                <span className="w-lbl">Origin Distance</span>
                <span className="w-val">{where.distance_from_victim_km || 0.8} km</span>
              </div>
              <div className="where-item">
                <span className="w-lbl">Coordinates</span>
                <span className="w-val mono">{where.lat?.toFixed(4)}, {where.lon?.toFixed(4)}</span>
              </div>
            </div>
            <button
              className="where-focus-map-btn"
              onClick={() => onSelectLocation?.(top_k_locations[0] || { lat: where.lat, lon: where.lon })}
            >
              📍 Center Map on Primary Target
            </button>
          </div>

          {/* WHEN SECTION */}
          <div className="five-d-box box-when">
            <div className="box-header">
              <span className="box-dim-tag tag-when">2. WHEN (TIME WINDOW)</span>
              <span className="box-meta-note">XGBoost Interception Model</span>
            </div>
            <div className="when-countdown-banner">
              <span className="countdown-icon">⏱</span>
              <span className="countdown-text">{when.operational_countdown || "Critical 30-60m cash-out window"}</span>
            </div>
            <div className="when-timing-grid">
              <div className="timing-col">
                <span className="t-lbl">Earliest</span>
                <span className="t-val">{when.earliest_minutes || 20}m</span>
              </div>
              <div className="timing-col peak-col">
                <span className="t-lbl">Peak Window</span>
                <span className="t-val text-yellow">{when.peak_minutes || 35}m</span>
              </div>
              <div className="timing-col">
                <span className="t-lbl">Latest</span>
                <span className="t-val">{when.latest_minutes || 50}m</span>
              </div>
            </div>
          </div>

          {/* AMOUNT SECTION */}
          <div className="five-d-box box-amount">
            <div className="box-header">
              <span className="box-dim-tag tag-amount">3. AMOUNT (LOSS &amp; CASHOUT)</span>
              <span className="box-meta-note">Learned Regressor Model</span>
            </div>
            <div className="amount-comparison-grid">
              <div className="amt-card">
                <span className="amt-lbl">Reported Fraud Loss</span>
                <span className="amt-num text-red">{formatINR(amount)}</span>
              </div>
              <div className="amt-card">
                <span className="amt-lbl">Predicted Cash-Out</span>
                <span className="amt-num text-yellow">
                  {formatINR(amt.estimated_cashout_amount || amt.predicted_cashout_amount || amount * 0.85)}
                </span>
                {amt.lower_bound && amt.upper_bound ? (
                  <span className="amt-sub" style={{ color: "var(--text-muted, #94a3b8)", fontSize: "0.82rem" }}>
                    Expected Range: {formatINR(amt.lower_bound)} – {formatINR(amt.upper_bound)}
                  </span>
                ) : (
                  <span className="amt-sub">After {money_trail?.hop_count || 2} mule cuts</span>
                )}
              </div>
            </div>
          </div>

          {/* WHY SECTION (SHAP EXPLAINABILITY) */}
          <div className="five-d-box box-why">
            <div className="box-header">
              <span className="box-dim-tag tag-why">4. WHY (SHAP EXPLAINABILITY)</span>
              <span className="box-meta-note">TreeExplainer Attribution</span>
            </div>
            <p className="why-summary-text">{why.summary || "High-risk cybercrime transaction pattern."}</p>
            
            {/* Human Readable Summary Drivers */}
            {why.key_drivers?.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "12px" }}>
                {why.key_drivers.map((driver, i) => (
                  <span key={i} style={{
                    background: "rgba(239, 68, 68, 0.12)",
                    border: "1px solid rgba(239, 68, 68, 0.3)",
                    padding: "3px 8px",
                    borderRadius: "4px",
                    fontSize: "0.8rem",
                    color: "#f87171"
                  }}>
                    {driver}
                  </span>
                ))}
              </div>
            )}

            {/* Feature contributions from SHAP or factor attributions */}
            {(why.explanation || why.factor_attributions)?.length > 0 && (
              <div className="why-factors-list">
                {(why.explanation || why.factor_attributions).map((f, i) => {
                  const badge = f.badge || (f.impact === "CRITICAL" ? "🔴" : f.impact === "HIGH" ? "🟠" : "🟡");
                  const label = f.human_label || f.factor || f.feature;
                  const desc = f.description || (f.contribution !== undefined ? `SHAP Contribution: ${(f.contribution > 0 ? "+" : "") + Number(f.contribution).toFixed(3)} (${f.direction || "impact"})` : "");
                  return (
                    <div key={i} className="why-factor-row">
                      <span className="factor-badge" style={{ fontSize: "1rem", minWidth: "32px", textAlign: "center" }}>
                        {badge}
                      </span>
                      <div className="factor-content">
                        <div className="factor-name" style={{ fontWeight: 600 }}>{label}</div>
                        <div className="factor-desc">{desc}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Extracted NLP Intelligence */}
          {(nlp_entities.nlp_upi_id || nlp_entities.nlp_bank_account) && (
            <div className="nlp-intel-banner">
              <span className="nlp-title">NLP Extracted Identifiers:</span>
              <div className="nlp-chips-wrap">
                {nlp_entities.nlp_upi_id && (
                  <span className="nlp-chip">UPI: {nlp_entities.nlp_upi_id}</span>
                )}
                {nlp_entities.nlp_bank_account && (
                  <span className="nlp-chip">Bank ACC: {nlp_entities.nlp_bank_account}</span>
                )}
                {nlp_entities.inferred_city && (
                  <span className="nlp-chip">City: {nlp_entities.inferred_city}</span>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── SubTab 2: Visual Money Trail ── */}
      {activeSubTab === "trail" && (
        <div className="dossier-scroll-body">
          <MoneyTrailFlow moneyTrail={money_trail} />
        </div>
      )}

      {/* ── SubTab 3: Top-K ATM Locations ── */}
      {activeSubTab === "topk" && (
        <div className="dossier-scroll-body">
          <TopKLocationsPanel
            locations={top_k_locations}
            onSelectLocation={onSelectLocation}
          />
        </div>
      )}

      {/* ── Footer Tactical Action Bar ── */}
      <div className="dossier-footer">
        <button
          type="button"
          className="dossier-btn-validate"
          onClick={onOpenOutcomeModal}
        >
          ⚖️ Validate Outcome / Intercept Log
        </button>

        <button
          type="button"
          className={`dossier-btn-copy ${copied ? "copied" : ""}`}
          onClick={handleCopyDispatch}
        >
          {copied ? "✓ Copied to Clipboard" : "📋 Copy Dispatch SOP"}
        </button>
      </div>
    </div>
  );
}
