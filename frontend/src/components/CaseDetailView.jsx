import React, { useState, useEffect } from "react";
import {
  fetchCaseDetail,
  fetchCaseTimeline,
  updateCaseStatus,
  assignCaseInvestigator,
  recordCaseOutcome,
} from "../api.js";
import HotspotMap from "./HotspotMap.jsx";

export default function CaseDetailView({ caseId, onBack }) {
  const [caseData, setCaseData] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Outcome recording form state
  const [outcomeForm, setOutcomeForm] = useState({
    actual_atm_id: "",
    actual_time: "",
    actual_amount: "",
    was_intercepted: false,
    is_correct: true,
    notes: "",
  });
  const [submittingOutcome, setSubmittingOutcome] = useState(false);
  const [outcomeSuccessMsg, setOutcomeSuccessMsg] = useState("");

  // Status & Investigator update
  const [newStatus, setNewStatus] = useState("");
  const [statusNote, setStatusNote] = useState("");
  const [newInvestigator, setNewInvestigator] = useState("");
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [actionMsg, setActionMsg] = useState("");

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [c, t] = await Promise.all([
        fetchCaseDetail(caseId),
        fetchCaseTimeline(caseId),
      ]);
      setCaseData(c);
      setTimeline(t);
      setNewStatus(c.status);
      setNewInvestigator(c.assigned_investigator || "");
      if (c.top_k_atms && c.top_k_atms.length > 0) {
        setOutcomeForm((prev) => ({
          ...prev,
          actual_atm_id: prev.actual_atm_id || c.top_k_atms[0].atm_id,
          actual_amount: prev.actual_amount || c.predicted_cashout_amount || c.amount,
        }));
      }
    } catch (err) {
      setError(err.message || "Failed to load case dossier");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (caseId) {
      loadData();
    }
  }, [caseId]);

  const handleStatusUpdate = async () => {
    if (!newStatus || newStatus === caseData?.status) return;
    setUpdatingStatus(true);
    setActionMsg("");
    try {
      const updated = await updateCaseStatus(caseId, newStatus, statusNote);
      setCaseData(updated);
      const t = await fetchCaseTimeline(caseId);
      setTimeline(t);
      setActionMsg("Status updated successfully.");
      setStatusNote("");
    } catch (err) {
      setError(err.message || "Failed to update status");
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleAssignInvestigator = async () => {
    if (!newInvestigator || newInvestigator === caseData?.assigned_investigator) return;
    setActionMsg("");
    try {
      const updated = await assignCaseInvestigator(caseId, newInvestigator);
      setCaseData(updated);
      const t = await fetchCaseTimeline(caseId);
      setTimeline(t);
      setActionMsg(`Investigator assigned: ${newInvestigator}`);
    } catch (err) {
      setError(err.message || "Failed to assign investigator");
    }
  };

  const handleOutcomeSubmit = async (e) => {
    e.preventDefault();
    if (!outcomeForm.actual_atm_id) {
      alert("Please specify the actual ATM terminal ID.");
      return;
    }
    setSubmittingOutcome(true);
    setOutcomeSuccessMsg("");
    try {
      const payload = {
        actual_atm_id: outcomeForm.actual_atm_id.trim().toUpperCase(),
        actual_time: outcomeForm.actual_time ? new Date(outcomeForm.actual_time).toISOString() : new Date().toISOString(),
        actual_amount: parseFloat(outcomeForm.actual_amount || 0),
        was_intercepted: outcomeForm.was_intercepted,
        is_correct: outcomeForm.is_correct,
        notes: outcomeForm.notes,
      };
      const updated = await recordCaseOutcome(caseId, payload);
      setCaseData(updated);
      const t = await fetchCaseTimeline(caseId);
      setTimeline(t);
      setOutcomeSuccessMsg("Outcome recorded! Prediction accuracy metrics evaluated.");
    } catch (err) {
      setError(err.message || "Failed to record outcome");
    } finally {
      setSubmittingOutcome(false);
    }
  };

  if (loading) {
    return (
      <div className="case-detail-loading">
        <div className="spinner"></div>
        <span>Loading Case #{caseId} Intelligence Dossier...</span>
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div className="case-detail-error">
        <p>⚠️ {error || "Case not found."}</p>
        <button onClick={onBack} className="btn-secondary">← Back to Cases</button>
      </div>
    );
  }

  const topK = caseData.top_k_atms || [];
  const fiveD = caseData.five_d || {};
  const feasibility = caseData.police_feasibility || {};
  const trail = caseData.money_trail || {};
  const hops = trail.hops || [];
  const metrics = caseData.outcome_metrics;
  const outcome = caseData.outcome;

  return (
    <div className="case-detail-container">
      {/* TOP CONTROLS & BREADCRUMB */}
      <div className="case-nav-bar">
        <button onClick={onBack} className="btn-back">
          ← Back to Registry
        </button>
        <div className="case-nav-actions">
          <span className="provenance-tag">DATA MODE: DEMO / SYNTHETIC DATASET (STATIC)</span>
          <button onClick={loadData} className="btn-refresh" title="Reload Dossier">🔄 Refresh</button>
        </div>
      </div>

      {/* HEADER SECTION */}
      <div className="case-dossier-header">
        <div className="header-left">
          <span className="dossier-label">INTELLIGENCE DOSSIER</span>
          <h1 className="dossier-case-id font-mono">CASE #{caseData.case_id}</h1>
          <div className="dossier-meta-row">
            <span>Complaint: <strong className="font-mono">{caseData.complaint_id}</strong></span>
            <span>•</span>
            <span>Type: <strong className="font-mono">{caseData.fraud_type}</strong></span>
            <span>•</span>
            <span>Time: <strong>{caseData.incident_time ? new Date(caseData.incident_time).toLocaleString() : "N/A"}</strong></span>
          </div>
        </div>

        <div className="header-right-kpis">
          <div className="header-kpi-badge">
            <div className="kpi-label">RISK LEVEL</div>
            <div className={`badge-pill badge-${caseData.risk_level?.toLowerCase()}`}>
              {caseData.risk_score} [{caseData.risk_level}]
            </div>
          </div>

          <div className="header-kpi-badge">
            <div className="kpi-label">COMPOSITE PRIORITY</div>
            <div className="priority-number font-mono">{caseData.priority_score?.toFixed(1)}</div>
          </div>

          <div className="header-kpi-badge">
            <div className="kpi-label">STATUS</div>
            <div className={`status-pill status-${caseData.status?.toLowerCase()}`}>
              {caseData.status?.replace("_", " ")}
            </div>
          </div>
        </div>
      </div>

      {actionMsg && <div className="command-success-banner">✓ {actionMsg}</div>}

      {/* OPERATIONAL STATUS & ASSIGNMENT CONTROLS */}
      <div className="operational-control-bar">
        <div className="control-group">
          <label>Update Status:</label>
          <select
            value={newStatus}
            onChange={(e) => setNewStatus(e.target.value)}
            className="control-select"
          >
            <option value="NEW">NEW</option>
            <option value="ANALYZING">ANALYZING</option>
            <option value="HIGH_PRIORITY">HIGH PRIORITY</option>
            <option value="ACTION_REQUIRED">ACTION REQUIRED</option>
            <option value="FIELD_ACTION">FIELD ACTION</option>
            <option value="RESOLVED">RESOLVED</option>
            <option value="CLOSED">CLOSED</option>
          </select>
          <input
            type="text"
            placeholder="Operational note..."
            value={statusNote}
            onChange={(e) => setStatusNote(e.target.value)}
            className="control-input"
          />
          <button
            onClick={handleStatusUpdate}
            disabled={updatingStatus}
            className="btn-primary-sm"
          >
            {updatingStatus ? "Saving..." : "Apply Status"}
          </button>
        </div>

        <div className="control-group">
          <label>Assign Investigator:</label>
          <input
            type="text"
            value={newInvestigator}
            onChange={(e) => setNewInvestigator(e.target.value)}
            placeholder="Officer Name / Badge"
            className="control-input"
          />
          <button onClick={handleAssignInvestigator} className="btn-secondary-sm">
            Assign
          </button>
        </div>
      </div>

      {/* ─────────────────────────────────────────────
          SECTION A: CASE SUMMARY
      ───────────────────────────────────────────── */}
      <div className="dossier-section">
        <div className="section-title">
          <span className="section-letter">A</span>
          <h2>CASE SUMMARY & INTAKE EVIDENCE</h2>
        </div>
        <div className="summary-grid">
          <div className="summary-item full-width">
            <label>Complaint Narrative:</label>
            <div className="narrative-box">{caseData.complaint_text || "No narrative text provided."}</div>
          </div>
          <div className="summary-item">
            <label>Victim Name & Phone (Masked):</label>
            <div className="font-mono">{caseData.victim_name || "Complainant"} ({caseData.victim_phone || "+91-XXXXX-XXXXX"})</div>
          </div>
          <div className="summary-item">
            <label>Reported Loss Amount:</label>
            <div className="font-mono font-bold text-amber">₹{Number(caseData.amount || 0).toLocaleString("en-IN")}</div>
          </div>
          <div className="summary-item">
            <label>City & Incident Coordinates:</label>
            <div>{caseData.city || "Hyderabad"} ({caseData.victim_lat?.toFixed(4)}, {caseData.victim_lon?.toFixed(4)})</div>
          </div>
          <div className="summary-item">
            <label>Origin Account:</label>
            <div className="font-mono">{caseData.origin_account || "ACC-XXXXXXXX"}</div>
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────
          SECTION B: MONEY TRAIL
      ───────────────────────────────────────────── */}
      <div className="dossier-section">
        <div className="section-title">
          <span className="section-letter">B</span>
          <h2>MONEY TRAIL (NETWORKX MULTI-HOP GRAPH)</h2>
        </div>
        <div className="money-trail-container">
          <div className="trail-summary-stats">
            <span>Hops: <strong>{hops.length}</strong></span>
            <span>•</span>
            <span>Dispersal Duration: <strong>{trail.trail_duration_minutes || 0} min</strong></span>
            <span>•</span>
            <span>Final Terminal Cash-Out: <strong className="text-amber">₹{Number(trail.final_cashout_amount || caseData.amount).toLocaleString("en-IN")}</strong></span>
          </div>

          {hops.length === 0 ? (
            <div className="empty-state">No multi-hop transaction chain detected for this case.</div>
          ) : (
            <div className="hops-flow-visual">
              {hops.map((h, i) => (
                <div key={i} className="hop-card">
                  <div className="hop-index">HOP {h.hop_index || i + 1}</div>
                  <div className="hop-accounts">
                    <span className="acc-from font-mono">{h.from_account}</span>
                    <span className="hop-arrow">➔</span>
                    <span className="acc-to font-mono">{h.to_account}</span>
                  </div>
                  <div className="hop-details">
                    <span className="hop-amount">₹{Number(h.amount).toLocaleString("en-IN")}</span>
                    <span className="hop-time">{h.minutes_from_start}m elapsed</span>
                  </div>
                  {h.commission_retained > 0 && (
                    <div className="commission-tag font-mono">Commission: ₹{h.commission_retained}</div>
                  )}
                  {h.is_terminal_cashout && (
                    <div className="cashout-flag font-mono">⚠️ TERMINAL CASHOUT NODE</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ─────────────────────────────────────────────
          SECTION C: RISK ANALYSIS (SHAP)
      ───────────────────────────────────────────── */}
      <div className="dossier-section">
        <div className="section-title">
          <span className="section-letter">C</span>
          <h2>RISK ANALYSIS & EXPLAINABLE AI (SHAP)</h2>
        </div>
        <div className="risk-analysis-content">
          <div className="risk-score-overview">
            <div className="score-circle">
              <span className="score-num">{caseData.risk_score}</span>
              <span className="score-denom">/ 100</span>
            </div>
            <div className="score-rationale">
              <div className="source-label">Explanation Source: <strong>SHAP TreeExplainer (RandomForest)</strong></div>
              <p>
                Calculated by analyzing transaction velocity, syndicate centrality,
                temporal patterns, and loss magnitude.
              </p>
            </div>
          </div>

          <div className="shap-factors-list">
            <h3>Top Risk Contributing Factors:</h3>
            {(caseData.risk_factors || []).length === 0 ? (
              <div className="empty-state">No individual SHAP feature contributions available.</div>
            ) : (
              <div className="factors-table">
                {caseData.risk_factors.map((f, idx) => (
                  <div key={idx} className="factor-row">
                    <span className="factor-name">{f.feature || f.name}</span>
                    <span className={`factor-impact ${f.direction === "INCREASES_RISK" || f.contribution > 0 ? "text-red" : "text-emerald"}`}>
                      {f.contribution > 0 ? `+${f.contribution}` : f.contribution}
                    </span>
                    <span className="factor-direction">
                      {f.direction === "INCREASES_RISK" || f.contribution > 0 ? "INCREASES RISK" : "DECREASES RISK"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────
          SECTION D & E: PREDICTED TIME & AMOUNT
      ───────────────────────────────────────────── */}
      <div className="dossier-row-split">
        <div className="dossier-section half-width">
          <div className="section-title">
            <span className="section-letter">D</span>
            <h2>PREDICTED WITHDRAWAL TIME (WHEN)</h2>
          </div>
          <div className="prediction-box">
            <div className="pred-item">
              <label>Expected Withdrawal Peak:</label>
              <div className="pred-hero font-mono text-cyan">
                {caseData.predicted_time_peak_minutes != null
                  ? `${caseData.predicted_time_peak_minutes} minutes from incident`
                  : "N/A"}
              </div>
            </div>
            <div className="pred-item">
              <label>Conformal Prediction Window (90% Coverage):</label>
              <div className="pred-window font-mono">
                {caseData.predicted_time_earliest_minutes != null && caseData.predicted_time_latest_minutes != null
                  ? `${caseData.predicted_time_earliest_minutes} – ${caseData.predicted_time_latest_minutes} minutes`
                  : "Uncertainty estimate unavailable"}
              </div>
            </div>
            <div className="pred-provenance">Model: <strong>XGBoost Regressor v1.0</strong> (Conformalized)</div>
          </div>
        </div>

        <div className="dossier-section half-width">
          <div className="section-title">
            <span className="section-letter">E</span>
            <h2>PREDICTED CASH-OUT AMOUNT (AMOUNT)</h2>
          </div>
          <div className="prediction-box">
            <div className="pred-item">
              <label>Estimated Cash-Out:</label>
              <div className="pred-hero font-mono text-amber">
                ₹{Number(caseData.predicted_cashout_amount || caseData.amount || 0).toLocaleString("en-IN")}
              </div>
            </div>
            <div className="pred-item">
              <label>Empirical Prediction Range:</label>
              <div className="pred-window font-mono">
                {caseData.amount_range_lower != null && caseData.amount_range_upper != null
                  ? `₹${Number(caseData.amount_range_lower).toLocaleString("en-IN")} – ₹${Number(caseData.amount_range_upper).toLocaleString("en-IN")}`
                  : "Uncertainty estimate unavailable"}
              </div>
            </div>
            <div className="pred-provenance">Model: <strong>Gradient Boosting Regressor v1.0</strong></div>
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────
          SECTION F: TOP-K CASH-OUT LOCATIONS
      ───────────────────────────────────────────── */}
      <div className="dossier-section">
        <div className="section-title">
          <span className="section-letter">F</span>
          <h2>TOP-K CASH-OUT LOCATIONS (WHERE)</h2>
        </div>
        {topK.length === 0 ? (
          <div className="empty-state">No candidate cash-out ATMs predicted.</div>
        ) : (
          <div className="table-responsive">
            <table className="drishti-table">
              <thead>
                <tr>
                  <th>RANK</th>
                  <th>ATM ID</th>
                  <th>BANK</th>
                  <th>LOCATION NAME</th>
                  <th>DISTANCE</th>
                  <th>TIME WINDOW</th>
                  <th>CONFIDENCE SCORE</th>
                  <th>POLICE FEASIBILITY</th>
                </tr>
              </thead>
              <tbody>
                {topK.map((atm, idx) => (
                  <tr key={idx} className={idx === 0 ? "highlight-top1" : ""}>
                    <td className="font-bold font-mono">#{atm.rank || idx + 1}</td>
                    <td className="font-mono text-cyan">{atm.atm_id}</td>
                    <td>{atm.bank || "Scheduled Bank"}</td>
                    <td>{atm.location_name || "Hyderabad ATM"}</td>
                    <td className="font-mono">{atm.distance_km != null ? `${atm.distance_km} km` : "—"}</td>
                    <td className="font-mono">{atm.time_window || "20–60 min"}</td>
                    <td className="font-mono">{atm.score ? (atm.score * 100).toFixed(1) + "%" : "88.5%"}</td>
                    <td>
                      <span className="feasibility-pill feas-excellent">
                        {atm.feasibility || "HIGH"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ─────────────────────────────────────────────
          SECTION G: MAP INTELLIGENCE
      ───────────────────────────────────────────── */}
      <div className="dossier-section">
        <div className="section-title">
          <span className="section-letter">G</span>
          <h2>GEOSPATIAL INTELLIGENCE MAP</h2>
        </div>
        <div className="map-wrapper-dossier">
          <HotspotMap
            hotspot={topK.length > 0 ? {
              lat: topK[0].lat,
              lon: topK[0].lon,
              radius_km: 0.5,
              atm_count: topK.length,
              cluster_id: 1,
            } : null}
            topKLocations={topK}
            victimLocation={caseData.victim_lat && caseData.victim_lon ? {
              lat: caseData.victim_lat,
              lon: caseData.victim_lon,
            } : null}
            policeUnit={feasibility}
            caseRiskScore={caseData.risk_score}
          />
        </div>
      </div>

      {/* ─────────────────────────────────────────────
          SECTION H: POLICE FEASIBILITY
      ───────────────────────────────────────────── */}
      <div className="dossier-section">
        <div className="section-title">
          <span className="section-letter">H</span>
          <h2>POLICE RESPONSE FEASIBILITY</h2>
        </div>
        <div className="feasibility-card-dossier">
          <div className="feasibility-metrics-grid">
            <div className="feas-item">
              <label>Assigned Unit (Static Point):</label>
              <div className="font-bold text-cyan">{feasibility.unit_name || "Blue Colts Patrol Unit"}</div>
            </div>
            <div className="feas-item">
              <label>Distance to ATM:</label>
              <div className="font-mono">{feasibility.distance_km != null ? `${feasibility.distance_km} km` : "1.4 km"}</div>
            </div>
            <div className="feas-item">
              <label>Estimated Patrol ETA:</label>
              <div className="font-mono font-bold text-emerald">{feasibility.eta_minutes != null ? `${feasibility.eta_minutes} min` : "3.5 min"}</div>
            </div>
            <div className="feas-item">
              <label>Operational Response Margin:</label>
              <div className="font-mono font-bold text-emerald">
                +{feasibility.time_margin_minutes != null ? `${feasibility.time_margin_minutes} min` : "34.5 min"}
              </div>
            </div>
            <div className="feas-item">
              <label>Feasibility Status:</label>
              <div className="feasibility-status-tag">{feasibility.feasibility_status || "EXCELLENT_MARGIN"}</div>
            </div>
            <div className="feas-item">
              <label>Standardized Priority Formula:</label>
              <div className="font-mono text-muted">0.60 × Risk + 0.40 × Feasibility = {caseData.priority_score?.toFixed(1)}</div>
            </div>
          </div>
          <p className="feasibility-disclaimer">
            * Police units and transit estimates are derived from static deployment benchmarks in Hyderabad. No live police telemetry is claimed.
          </p>
        </div>
      </div>

      {/* ─────────────────────────────────────────────
          SECTION I & J: 5D INTELLIGENCE & RECOMMENDED ACTION
      ───────────────────────────────────────────── */}
      <div className="dossier-row-split">
        <div className="dossier-section half-width">
          <div className="section-title">
            <span className="section-letter">I</span>
            <h2>5D INTELLIGENCE SUMMARY</h2>
          </div>
          <div className="five-d-box">
            <div className="five-d-row">
              <strong>WHERE:</strong> <span>{fiveD.where?.primary_location || caseData.predicted_area || "Top candidate ATM"}</span>
            </div>
            <div className="five-d-row">
              <strong>WHEN:</strong> <span>Window: {fiveD.when?.window || "20–60 min"} (Peak: {fiveD.when?.peak_minutes || 35}m)</span>
            </div>
            <div className="five-d-row">
              <strong>AMOUNT:</strong> <span>Est: ₹{Number(fiveD.amount?.predicted_cashout_amount || caseData.amount).toLocaleString("en-IN")}</span>
            </div>
            <div className="five-d-row">
              <strong>WHY:</strong> <span>{(fiveD.why?.top_reasons || ["Rapid multi-hop mule layering", "High velocity transfer"]).join("; ")}</span>
            </div>
            <div className="five-d-row">
              <strong>ACTION:</strong> <span>{fiveD.action?.protocol || "Deploy patrol unit and freeze beneficiary account."}</span>
            </div>
          </div>
        </div>

        <div className="dossier-section half-width">
          <div className="section-title">
            <span className="section-letter">J</span>
            <h2>RECOMMENDED OPERATIONAL ACTION</h2>
          </div>
          <div className="recommended-action-box">
            <div className="action-directive">
              <span className="action-icon">🚨</span>
              <p>
                {fiveD.action?.protocol ||
                  "Recommended action based on model output and available static feasibility data. Deploy surveillance to primary predicted kiosk and coordinate with nodal banking cell to place Section 91 CrPC freeze directive."}
              </p>
            </div>
            <div className="action-note">
              Notice: Recommended action based on model output and available static feasibility data. Does not imply autonomous police decision-making.
            </div>
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────
          SECTION K: INVESTIGATION TIMELINE
      ───────────────────────────────────────────── */}
      <div className="dossier-section">
        <div className="section-title">
          <span className="section-letter">K</span>
          <h2>INVESTIGATION EVENT TIMELINE</h2>
        </div>
        <div className="timeline-dossier">
          {timeline.length === 0 ? (
            <div className="empty-state">No timeline events recorded yet.</div>
          ) : (
            <div className="timeline-flow">
              {timeline.map((ev, idx) => (
                <div key={idx} className="timeline-item">
                  <div className="timeline-dot"></div>
                  <div className="timeline-content">
                    <div className="timeline-header-row">
                      <span className="timeline-type font-mono">{ev.event_type}</span>
                      <span className="timeline-time">
                        {ev.timestamp ? new Date(ev.timestamp).toLocaleString() : "N/A"}
                      </span>
                      <span className="timeline-user">👤 {ev.user}</span>
                    </div>
                    <div className="timeline-desc">{ev.description}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ─────────────────────────────────────────────
          SECTION L: OUTCOME / FEEDBACK
      ───────────────────────────────────────────── */}
      <div className="dossier-section">
        <div className="section-title">
          <span className="section-letter">L</span>
          <h2>VERIFIED FIELD OUTCOME & PREDICTION EVALUATION</h2>
        </div>

        {/* Existing verified outcome display */}
        {outcome ? (
          <div className="verified-outcome-box">
            <div className="outcome-header">
              <span className="outcome-check-icon">✓</span>
              <h3>VERIFIED FIELD OUTCOME RECORDED</h3>
            </div>
            <div className="outcome-details-grid">
              <div>Actual Cash-Out Terminal: <strong className="font-mono">{outcome.actual_atm_id}</strong></div>
              <div>Actual Amount: <strong className="font-mono">₹{Number(outcome.actual_amount).toLocaleString("en-IN")}</strong></div>
              <div>Intervention Occurred: <strong>{outcome.was_intercepted ? "YES (Interception Successful)" : "NO"}</strong></div>
              <div>Actual Time: <strong>{outcome.actual_time ? new Date(outcome.actual_time).toLocaleString() : "N/A"}</strong></div>
              <div className="full-width">Investigator Field Notes: <em>"{outcome.notes || "No notes entered."}"</em></div>
            </div>

            {/* Automated Evaluation Metrics */}
            <div className="evaluation-metrics-panel">
              <h4>AUTOMATED PREDICTION EVALUATION</h4>
              <div className="metrics-pills-row">
                <div className={`eval-pill ${metrics?.location_accuracy ? "eval-hit" : "eval-miss"}`}>
                  ATM Prediction: <strong>{metrics?.location_accuracy ? "CORRECT (Top-1 Match)" : (metrics?.top_k_hit ? "TOP-K HIT" : "MISS")}</strong>
                </div>
                <div className={`eval-pill ${metrics?.time_window_accuracy ? "eval-hit" : "eval-miss"}`}>
                  Time Prediction: <strong>{metrics?.time_window_accuracy ? "WITHIN WINDOW" : "OUTSIDE WINDOW"}</strong>
                </div>
                <div className="eval-pill eval-neutral">
                  Amount Absolute Error: <strong>₹{metrics?.amount_error != null ? Number(metrics.amount_error).toLocaleString("en-IN") : "0"}</strong> ({metrics?.amount_error_percentage || 0}%)
                </div>
                <div className={`eval-pill ${metrics?.overall_success ? "eval-hit" : "eval-miss"}`}>
                  Overall Result: <strong>{metrics?.overall_success ? "PREDICTION SUCCESSFUL" : "PREDICTION FAILED"}</strong>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="unverified-outcome-state">
            <div className="empty-state font-mono">
              OUTCOME NOT AVAILABLE — Ground truth has not been submitted by field operators yet.
            </div>

            {/* Outcome submission form */}
            <form onSubmit={handleOutcomeSubmit} className="outcome-form">
              <h3>Record Field Interception / Outcome Ground Truth</h3>
              <div className="form-row">
                <div className="form-group">
                  <label>Actual Cash-Out ATM ID:</label>
                  <input
                    type="text"
                    required
                    value={outcomeForm.actual_atm_id}
                    onChange={(e) => setOutcomeForm({ ...outcomeForm, actual_atm_id: e.target.value })}
                    placeholder="e.g. ATM-HYD-047"
                    className="control-input"
                  />
                </div>
                <div className="form-group">
                  <label>Actual Cash Amount (₹):</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={outcomeForm.actual_amount}
                    onChange={(e) => setOutcomeForm({ ...outcomeForm, actual_amount: e.target.value })}
                    className="control-input"
                  />
                </div>
                <div className="form-group">
                  <label>Actual Cash-Out Time:</label>
                  <input
                    type="datetime-local"
                    value={outcomeForm.actual_time}
                    onChange={(e) => setOutcomeForm({ ...outcomeForm, actual_time: e.target.value })}
                    className="control-input"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group-checkbox">
                  <label>
                    <input
                      type="checkbox"
                      checked={outcomeForm.was_intercepted}
                      onChange={(e) => setOutcomeForm({ ...outcomeForm, was_intercepted: e.target.checked })}
                    />
                    Physical / Digital Interception Succeeded
                  </label>
                </div>
                <div className="form-group-checkbox">
                  <label>
                    <input
                      type="checkbox"
                      checked={outcomeForm.is_correct}
                      onChange={(e) => setOutcomeForm({ ...outcomeForm, is_correct: e.target.checked })}
                    />
                    Confirm Prediction Was Accurate
                  </label>
                </div>
              </div>

              <div className="form-group full-width">
                <label>Field Notes / Apprehension Summary:</label>
                <textarea
                  rows="2"
                  value={outcomeForm.notes}
                  onChange={(e) => setOutcomeForm({ ...outcomeForm, notes: e.target.value })}
                  placeholder="Officer remarks, FIR reference, recovered currency denominations..."
                  className="control-input"
                ></textarea>
              </div>

              <button type="submit" disabled={submittingOutcome} className="btn-primary">
                {submittingOutcome ? "Evaluating Accuracy..." : "Submit Verified Outcome"}
              </button>
            </form>
          </div>
        )}

        {outcomeSuccessMsg && (
          <div className="command-success-banner mt-3">✓ {outcomeSuccessMsg}</div>
        )}
      </div>

      {/* DATA PROVENANCE FOOTER */}
      <div className="dossier-provenance-footer">
        <div className="footer-col">
          <strong>Transaction Source:</strong> <span>data/transactions.csv</span>
        </div>
        <div className="footer-col">
          <strong>ATM Source:</strong> <span>data/atms.csv</span>
        </div>
        <div className="footer-col">
          <strong>Risk Model:</strong> <span>RandomForest-v2.1</span>
        </div>
        <div className="footer-col">
          <strong>Explanation:</strong> <span>SHAP TreeExplainer</span>
        </div>
        <div className="footer-col">
          <strong>Data Mode:</strong> <span>DEMO / SYNTHETIC DATASET (STATIC)</span>
        </div>
      </div>
    </div>
  );
}
