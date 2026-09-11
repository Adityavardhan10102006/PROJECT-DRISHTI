import React, { useState, useEffect } from "react";
import { fetchCases } from "../api.js";

export default function CasesListView({ onSelectCase, onNavigate }) {
  const [cases, setCases] = useState([]);
  const [riskFilter, setRiskFilter] = useState("");
  const [specialFilter, setSpecialFilter] = useState("all"); // all | critical_top10 | active | recent
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadCases = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCases({
        risk_level: riskFilter || undefined,
        search: searchQuery.trim() || undefined,
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

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      loadCases();
    }, 280);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Derived filtered & sorted cases
  let filteredCases = [...cases];

  const criticalCount = cases.filter(
    (c) => c.risk_level === "CRITICAL" || c.risk_level === "HIGH"
  ).length;

  const activeCount = cases.filter(
    (c) => c.status !== "RESOLVED" && c.status !== "CLOSED"
  ).length;

  if (specialFilter === "critical_top10") {
    filteredCases = filteredCases
      .filter((c) => c.risk_level === "CRITICAL" || c.risk_level === "HIGH")
      .sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0))
      .slice(0, 10);
  } else if (specialFilter === "active") {
    filteredCases = filteredCases.filter(
      (c) => c.status !== "RESOLVED" && c.status !== "CLOSED"
    );
  } else if (specialFilter === "recent") {
    filteredCases = filteredCases.sort(
      (a, b) => new Date(b.created_at || b.incident_time || 0) - new Date(a.created_at || a.incident_time || 0)
    );
  }

  // Export JSON functionality
  const handleExportRegistry = () => {
    const payload = {
      export_timestamp: new Date().toISOString(),
      platform: "PROJECT DRISHTI — Cybercrime Investigation Registry",
      filter: { riskFilter, specialFilter, searchQuery },
      case_count: filteredCases.length,
      cases: filteredCases,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `DRISHTI_CASE_REGISTRY_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="overview-container">
      {/* ── HEADER ── */}
      <div className="view-header" style={{ flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1 className="view-title">Investigation Dossiers</h1>
          <p className="view-subtitle">
            Cybercrime Complaint Registry &amp; Multi-Hop Analysis Ledger
          </p>
        </div>

        <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
          {onNavigate && (
            <button
              type="button"
              className="chip-btn"
              onClick={() => onNavigate("pipeline", "CASE-001-UPI-CRITICAL")}
              style={{
                fontSize: "12px",
                padding: "6px 12px",
                borderColor: "rgba(229,9,20,0.4)",
                color: "var(--red-bright)",
                background: "rgba(229,9,20,0.1)",
              }}
            >
              ⚡ 5D PIPELINE
            </button>
          )}

          <button
            type="button"
            className="chip-btn"
            onClick={loadCases}
            title="Refresh cases from backend"
          >
            🔄 REFRESH
          </button>

          <button
            type="button"
            className="chip-btn"
            onClick={handleExportRegistry}
            title="Export filtered case registry as JSON"
          >
            📥 EXPORT REGISTRY
          </button>

          <button
            className="btn-primary-action"
            onClick={() => onSelectCase("CASE-001-UPI-CRITICAL")}
            title="Load the primary 3-hop demonstration case"
          >
            <span>PRIMARY DEMO CASE</span>
            <span>→</span>
          </button>
        </div>
      </div>

      {/* ── SEARCH & FILTER CONTROLS ── */}
      <div className="cases-controls-bar" style={{ flexWrap: "wrap", gap: "12px" }}>
        <div className="search-field">
          <span className="search-field-icon">🔍</span>
          <input
            type="text"
            placeholder="Search by Case ID, type, zone, amount..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", marginRight: "8px" }}
            >
              ✕
            </button>
          )}
        </div>

        {/* Special Filter Buttons */}
        <div className="filter-chips-group">
          <button
            type="button"
            className={`chip-btn ${specialFilter === "all" && riskFilter === "" ? "active" : ""}`}
            onClick={() => { setSpecialFilter("all"); setRiskFilter(""); }}
          >
            ALL ({cases.length})
          </button>

          <button
            type="button"
            className={`chip-btn ${specialFilter === "critical_top10" ? "active" : ""}`}
            onClick={() => {
              setSpecialFilter("critical_top10");
              setRiskFilter("");
            }}
            style={{
              borderColor: "rgba(229,9,20,0.4)",
              color: specialFilter === "critical_top10" ? "#fff" : "var(--red-bright)",
            }}
            title="Show top 10 critical & high risk cases sorted by risk descending"
          >
            🚨 CRITICAL ONLY ({criticalCount > 10 ? 10 : criticalCount})
          </button>

          <button
            type="button"
            className={`chip-btn ${specialFilter === "active" ? "active" : ""}`}
            onClick={() => {
              setSpecialFilter("active");
              setRiskFilter("");
            }}
          >
            ACTIVE ({activeCount})
          </button>

          <button
            type="button"
            className={`chip-btn ${specialFilter === "recent" ? "active" : ""}`}
            onClick={() => {
              setSpecialFilter("recent");
            }}
          >
            RECENT
          </button>
        </div>

        {/* Standard Risk Tier Filter Chips */}
        <div className="filter-chips-group">
          <span style={{ fontSize: "11px", color: "var(--text-muted)", marginRight: "4px" }}>Tier:</span>
          {["CRITICAL", "HIGH", "MEDIUM", "LOW"].map((lvl) => (
            <button
              key={lvl}
              type="button"
              className={`chip-btn ${riskFilter === lvl ? "active" : ""}`}
              onClick={() => {
                setSpecialFilter("all");
                setRiskFilter(riskFilter === lvl ? "" : lvl);
              }}
              style={{ fontSize: "10.5px", padding: "3px 8px" }}
            >
              {lvl}
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
                <th style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: "center", padding: "32px", color: "var(--text-muted)" }}>
                    Loading investigation registry...
                  </td>
                </tr>
              ) : filteredCases.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: "center", padding: "32px", color: "var(--text-muted)" }}>
                    No matching cases found.
                  </td>
                </tr>
              ) : (
                filteredCases.map((c) => {
                  const riskCls =
                    c.risk_level === "CRITICAL"
                      ? "badge-risk-critical"
                      : c.risk_level === "HIGH"
                      ? "badge-risk-high"
                      : c.risk_level === "MEDIUM"
                      ? "badge-risk-medium"
                      : "badge-risk-low";

                  const hopCount = c.money_trail?.hops?.length || 3;

                  return (
                    <tr key={c.case_id} onClick={() => onSelectCase(c.case_id)}>
                      <td className="font-mono" style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                        #{c.case_id}
                      </td>
                      <td style={{ fontWeight: 500 }}>
                        {c.fraud_type
                          ? c.fraud_type.replace("_", " ").toUpperCase()
                          : "CYBER FRAUD"}
                      </td>
                      <td className="font-mono text-amber">
                        ₹{Number(c.amount || 0).toLocaleString("en-IN")}
                      </td>
                      <td>{c.city || "Hyderabad"}</td>
                      <td className="font-mono" style={{ fontSize: "11px", color: "var(--text-secondary)" }}>
                        {hopCount}-hop layer
                      </td>
                      <td>
                        <span className={`badge-tag ${riskCls}`}>
                          {c.risk_level || "MEDIUM"}
                          {c.risk_score != null ? ` (${Math.round(c.risk_score)})` : ""}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                          {c.status || "NEW"}
                        </span>
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <div style={{ display: "inline-flex", gap: "6px" }}>
                          {onNavigate && (
                            <button
                              type="button"
                              className="btn-table-action"
                              style={{ color: "var(--red-bright)", borderColor: "rgba(229,9,20,0.3)" }}
                              onClick={(e) => {
                                e.stopPropagation();
                                onNavigate("pipeline", c.case_id);
                              }}
                              title="Inspect 5D Predictive Intelligence Pipeline"
                            >
                              5D Pipeline
                            </button>
                          )}
                          <button
                            type="button"
                            className="btn-table-action"
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectCase(c.case_id);
                            }}
                          >
                            Dossier
                          </button>
                        </div>
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
