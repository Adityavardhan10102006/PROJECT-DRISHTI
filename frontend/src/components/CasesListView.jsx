import React, { useState, useEffect } from "react";
import { fetchCases } from "../api.js";

export default function CasesListView({ onSelectCase }) {
  const [cases, setCases] = useState([]);
  const [riskFilter, setRiskFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadCases = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCases({
        risk_level: riskFilter || undefined,
        search: searchQuery || undefined,
        limit: 50,
      });
      setCases(data || []);
    } catch (err) {
      setError(err.message || "Failed to load cases");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, [riskFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadCases();
  };

  return (
    <div className="overview-container">
      {/* ── HEADER ── */}
      <div className="view-header">
        <div>
          <h1 className="view-title">Investigation Dossiers</h1>
          <p className="view-subtitle">
            Cybercrime Complaint Registry &amp; Multi-Hop Analysis Ledger
          </p>
        </div>

        <button
          className="btn-primary-action"
          onClick={() => onSelectCase("DR-2026-1001")}
          title="Load the primary 3-hop demonstration case"
        >
          <span>DEMO CASE #DR-2026-1001</span>
          <span>→</span>
        </button>
      </div>

      {/* ── SEARCH & FILTER CONTROLS ── */}
      <div className="cases-controls-bar">
        <form onSubmit={handleSearchSubmit} className="search-field">
          <span className="search-field-icon">🔍</span>
          <input
            type="text"
            placeholder="Search by Case ID, type, zone, amount..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </form>

        <div className="filter-chips-group">
          <span style={{ fontSize: "11.5px", color: "var(--text-muted)", marginRight: "4px" }}>Filter:</span>
          {["", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((lvl) => (
            <button
              key={lvl}
              type="button"
              className={`chip-btn ${riskFilter === lvl ? "active" : ""}`}
              onClick={() => setRiskFilter(lvl)}
            >
              {lvl === "" ? "ALL" : lvl}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="panel-card" style={{ borderColor: "var(--risk-high-bd)", background: "var(--risk-high-bg)", color: "var(--risk-high)", marginBottom: "16px" }}>
          <span>⚠️ {error}</span>
          <button onClick={loadCases} style={{ marginLeft: "12px", background: "none", border: "none", color: "inherit", textDecoration: "underline", cursor: "pointer" }}>
            Retry
          </button>
        </div>
      )}

      {/* ── CASES TABLE ── */}
      <div className="panel-card" style={{ padding: 0, overflow: "hidden" }}>
        <div className="table-responsive">
          <table className="drishti-table">
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Fraud Typology</th>
                <th>Loss Amount</th>
                <th>Jurisdiction</th>
                <th>Mule Trail</th>
                <th>Risk Tier</th>
                <th>Pipeline Status</th>
                <th style={{ textAlign: "right" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: "center", padding: "32px", color: "var(--text-muted)" }}>
                    Loading investigation registry...
                  </td>
                </tr>
              ) : cases.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: "center", padding: "32px", color: "var(--text-muted)" }}>
                    No matching cases found.
                  </td>
                </tr>
              ) : (
                cases.map((c) => {
                  const riskCls =
                    c.risk_level === "CRITICAL"
                      ? "badge-risk-critical"
                      : c.risk_level === "HIGH"
                      ? "badge-risk-high"
                      : c.risk_level === "MEDIUM"
                      ? "badge-risk-medium"
                      : "badge-risk-low";

                  return (
                    <tr key={c.case_id} onClick={() => onSelectCase(c.case_id)}>
                      <td className="font-mono" style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                        #{c.case_id}
                      </td>
                      <td style={{ fontWeight: 500 }}>
                        {c.fraud_type
                          ? c.fraud_type.replace("_", " ").toUpperCase()
                          : "UPI FRAUD"}
                      </td>
                      <td className="font-mono text-amber" style={{ fontWeight: 600 }}>
                        ₹{Number(c.amount || 0).toLocaleString("en-IN")}
                      </td>
                      <td>{c.city || "Hyderabad"}</td>
                      <td className="font-mono text-muted">
                        {c.hop_count || (c.case_id === "DR-2026-1001" ? 3 : 2)} Hops
                      </td>
                      <td>
                        <span className={`badge-tag ${riskCls}`}>
                          {c.risk_level || "MEDIUM"}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                          {c.predicted_cashout_amount ? "PREDICTED" : c.status || "NEW"}
                        </span>
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <button
                          className="btn-table-action"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectCase(c.case_id);
                          }}
                        >
                          Open Dossier
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
