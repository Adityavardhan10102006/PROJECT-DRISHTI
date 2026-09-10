import React, { useState, useEffect } from "react";
import { fetchCases } from "../api.js";

export default function AlertsCenterView({ onSelectCase, onNavigate }) {
  const [filter, setFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [resolvedIds, setResolvedIds] = useState(new Set());
  const [dispatchedIds, setDispatchedIds] = useState(new Set());

  useEffect(() => {
    async function loadAlerts() {
      setLoading(true);
      try {
        const data = await fetchCases({ limit: 50 });
        setCases(data);
      } catch (err) {
        console.error("Failed to load cases for alerts:", err);
      } finally {
        setLoading(false);
      }
    }
    loadAlerts();
  }, []);

  const handleDispatch = (caseId, e) => {
    e.stopPropagation();
    setDispatchedIds((prev) => new Set([...prev, caseId]));
  };

  const handleResolve = (caseId, e) => {
    e.stopPropagation();
    setResolvedIds((prev) => new Set([...prev, caseId]));
  };

  const filteredCases = cases.filter((c) => {
    const isResolved = resolvedIds.has(c.case_id) || c.status === "RESOLVED" || c.status === "CLOSED";
    
    // Filter condition
    if (filter === "RESOLVED" && !isResolved) return false;
    if (filter !== "ALL" && filter !== "RESOLVED") {
      if (isResolved) return false;
      if (c.risk_level?.toUpperCase() !== filter) return false;
    }

    // Search condition
    if (search.trim()) {
      const q = search.toLowerCase();
      const matchId = c.case_id?.toLowerCase().includes(q);
      const matchComp = c.complaint_id?.toLowerCase().includes(q);
      const matchType = c.fraud_type?.toLowerCase().includes(q);
      const matchAtm = c.predicted_atm_id?.toLowerCase().includes(q);
      return matchId || matchComp || matchType || matchAtm;
    }

    return true;
  });

  const criticalCount = cases.filter((c) => c.risk_level === "CRITICAL" && !resolvedIds.has(c.case_id)).length;
  const highCount = cases.filter((c) => c.risk_level === "HIGH" && !resolvedIds.has(c.case_id)).length;
  const mediumCount = cases.filter((c) => c.risk_level === "MEDIUM" && !resolvedIds.has(c.case_id)).length;
  const totalResolved = cases.filter((c) => resolvedIds.has(c.case_id) || c.status === "RESOLVED").length;

  return (
    <div className="alerts-center-container">
      {/* Header */}
      <div className="alerts-center-header">
        <div>
          <h1 className="alerts-title">TACTICAL ALERT MATRIX & THREAT TRIAGE</h1>
          <p className="alerts-subtitle">
            Real-time cyber-mule cash-out predictions prioritized by time window margin and interception feasibility
          </p>
        </div>
        <div className="alerts-summary-strip">
          <div className="alert-stat-pill pill-critical">
            <span className="stat-num">{criticalCount}</span>
            <span className="stat-lbl">CRITICAL</span>
          </div>
          <div className="alert-stat-pill pill-high">
            <span className="stat-num">{highCount}</span>
            <span className="stat-lbl">HIGH</span>
          </div>
          <div className="alert-stat-pill pill-medium">
            <span className="stat-num">{mediumCount}</span>
            <span className="stat-lbl">MEDIUM</span>
          </div>
          <div className="alert-stat-pill pill-resolved">
            <span className="stat-num">{totalResolved}</span>
            <span className="stat-lbl">RESOLVED</span>
          </div>
        </div>
      </div>

      {/* Control Bar: Filter Pills + Search */}
      <div className="alerts-control-bar">
        <div className="filter-pill-group">
          {["ALL", "CRITICAL", "HIGH", "MEDIUM", "RESOLVED"].map((lvl) => (
            <button
              key={lvl}
              className={`filter-btn ${filter === lvl ? "active" : ""}`}
              onClick={() => setFilter(lvl)}
            >
              {lvl}
            </button>
          ))}
        </div>
        <div className="alert-search-box">
          <input
            type="text"
            placeholder="Search alerts by Case ID, Terminal, Fraud type..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="alert-search-input"
          />
          {search && (
            <button className="clear-search-btn" onClick={() => setSearch("")}>
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Alert Cards Feed */}
      {loading ? (
        <div className="alerts-loading-state">
          <div className="spinner"></div>
          <span>Streaming active threat matrix...</span>
        </div>
      ) : filteredCases.length === 0 ? (
        <div className="alerts-empty-state">
          <span className="empty-icon">🛡️</span>
          <h3>No Threat Alerts in Current Filter</h3>
          <p>All active cybercrime cash-out incidents in this category have been intercepted or resolved.</p>
          <button className="btn-secondary" onClick={() => setFilter("ALL")}>
            Reset Filter to ALL
          </button>
        </div>
      ) : (
        <div className="alert-cards-grid">
          {filteredCases.map((c) => {
            const isResolved = resolvedIds.has(c.case_id) || c.status === "RESOLVED";
            const isDispatched = dispatchedIds.has(c.case_id);
            const riskLevel = c.risk_level || "MEDIUM";

            return (
              <div
                key={c.case_id}
                className={`tactical-alert-card border-${riskLevel.toLowerCase()} ${
                  isResolved ? "card-resolved" : ""
                }`}
                onClick={() => onSelectCase(c.case_id)}
              >
                {/* Top strip */}
                <div className="alert-card-top">
                  <div className="alert-badge-group">
                    <span className={`alert-severity-badge severity-${riskLevel.toLowerCase()}`}>
                      {riskLevel} THREAT
                    </span>
                    <span className="alert-case-tag">{c.case_id}</span>
                    <span className="alert-type-tag">{c.fraud_type?.toUpperCase().replace("_", " ")}</span>
                  </div>
                  <span className="alert-timestamp">
                    {c.created_at ? new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "ACTIVE"}
                  </span>
                </div>

                {/* Core Details Grid */}
                <div className="alert-details-grid">
                  <div className="detail-box">
                    <span className="d-label">TARGET ATM / ZONE</span>
                    <span className="d-val text-cyan font-bold">
                      {c.predicted_atm_id || "Banjara Hills ATM Cluster"}
                    </span>
                    <span className="d-sub">Jurisdiction: Jubilee Hills PS</span>
                  </div>

                  <div className="detail-box">
                    <span className="d-label">ESTIMATED CASH-OUT</span>
                    <span className="d-val text-emerald font-mono font-bold">
                      ₹{c.predicted_cashout_amount ? Math.round(c.predicted_cashout_amount).toLocaleString("en-IN") : (c.amount ? Math.round(c.amount * 0.9).toLocaleString("en-IN") : "82,500")}
                    </span>
                    <span className="d-sub">Loss: ₹{c.amount ? Math.round(c.amount).toLocaleString("en-IN") : "90,000"}</span>
                  </div>

                  <div className="detail-box">
                    <span className="d-label">ARRIVAL WINDOW</span>
                    <span className="d-val text-amber font-mono font-bold">
                      ⏱ {c.predicted_withdrawal_window || "30–50 min"}
                    </span>
                    <span className="d-sub">Conformal Band: ±10.6m</span>
                  </div>

                  <div className="detail-box">
                    <span className="d-label">TACTICAL FEASIBILITY</span>
                    <span className="d-val text-cyan font-mono font-bold">
                      {c.police_feasibility_score ? `${Math.round(c.police_feasibility_score)}/100` : "84/100"}
                    </span>
                    <span className="d-sub">Blue Colts Rapid Unit 04</span>
                  </div>
                </div>

                {/* Directive / SOP */}
                <div className="alert-sop-strip">
                  <span className="sop-label">RECOMMENDED PROTOCOL:</span>
                  <span className="sop-text">
                    {riskLevel === "CRITICAL"
                      ? "Deploy Blue Colts rapid patrol to target ATM terminal. Execute immediate Section 91 CrPC CCTV preservation."
                      : "Correlate beneficiary node with National Cyber Crime Reporting Portal (NCRP) records and flag transaction."}
                  </span>
                </div>

                {/* Action Buttons */}
                <div className="alert-action-footer">
                  <button
                    className="btn-alert-dossier"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectCase(c.case_id);
                    }}
                  >
                    📄 Open Dossier
                  </button>
                  {!isResolved ? (
                    <>
                      <button
                        className={`btn-alert-dispatch ${isDispatched ? "btn-dispatched" : ""}`}
                        onClick={(e) => handleDispatch(c.case_id, e)}
                        disabled={isDispatched}
                      >
                        {isDispatched ? "✓ Unit Dispatched" : "🚔 Dispatch Patrol"}
                      </button>
                      <button
                        className="btn-alert-resolve"
                        onClick={(e) => handleResolve(c.case_id, e)}
                      >
                        ✓ Mark Handled
                      </button>
                    </>
                  ) : (
                    <span className="resolved-status-tag">✓ Interception Resolved</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
