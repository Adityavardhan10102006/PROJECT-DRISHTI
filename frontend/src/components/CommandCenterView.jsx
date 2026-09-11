import React, { useState, useEffect } from "react";
import { fetchCaseStats, fetchCases } from "../api.js";

export default function CommandCenterView({ onSelectCase, onNavigate }) {
  const [stats, setStats] = useState(null);
  const [cases, setCases] = useState([]);
  const [activeFilter, setActiveFilter] = useState("all"); // all | critical_top10 | active | recent
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsData, casesData] = await Promise.all([
        fetchCaseStats().catch(() => null),
        fetchCases({ limit: 50 }),
      ]);
      setStats(statsData);
      setCases(casesData || []);
    } catch (err) {
      setError(err.message || "Failed to load intelligence summary");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Compute metrics from actual cases
  const totalCases = stats?.total_cases ?? cases.length;
  const criticalCases = cases.filter((c) => c.risk_level === "CRITICAL");
  const highRiskCases = cases.filter((c) => c.risk_level === "HIGH" || c.risk_level === "CRITICAL");
  const activeCasesList = cases.filter((c) => c.status !== "RESOLVED" && c.status !== "CLOSED");
  const casesWithPredictions = cases.filter(
    (c) => (c.top_k_atms && c.top_k_atms.length > 0) || c.predicted_cashout_amount > 0 || c.predicted_area
  );
  const highFeasibilityCases = cases.filter(
    (c) =>
      c.police_feasibility?.feasibility_status === "HIGH" ||
      (c.police_feasibility?.time_margin_minutes != null && c.police_feasibility.time_margin_minutes > 10) ||
      (c.priority_score != null && c.priority_score >= 70)
  );

  const criticalCasesCount = highRiskCases.length;
  const activeCasesCount = activeCasesList.length;
  const predictedCashouts = casesWithPredictions.length;
  const highFeasibilityCount = highFeasibilityCases.length;

  // Filter & Rank cases
  let displayedCases = [...cases];

  // Search filter
  if (searchQuery.trim()) {
    const q = searchQuery.toLowerCase().trim();
    displayedCases = displayedCases.filter(
      (c) =>
        (c.case_id && c.case_id.toLowerCase().includes(q)) ||
        (c.fraud_type && c.fraud_type.toLowerCase().includes(q)) ||
        (c.city && c.city.toLowerCase().includes(q)) ||
        (c.predicted_area && c.predicted_area.toLowerCase().includes(q)) ||
        (c.risk_level && c.risk_level.toLowerCase().includes(q)) ||
        (c.amount && String(c.amount).includes(q))
    );
  }

  // Active quick filter
  if (activeFilter === "critical_top10") {
    displayedCases = displayedCases
      .filter((c) => c.risk_level === "CRITICAL" || c.risk_level === "HIGH")
      .sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0))
      .slice(0, 10);
  } else if (activeFilter === "active") {
    displayedCases = displayedCases.filter(
      (c) => c.status !== "RESOLVED" && c.status !== "CLOSED"
    );
  } else if (activeFilter === "recent") {
    displayedCases = displayedCases.sort(
      (a, b) => new Date(b.created_at || b.incident_time || 0) - new Date(a.created_at || a.incident_time || 0)
    );
  } else if (activeFilter === "high_risk") {
    displayedCases = displayedCases.filter((c) => c.risk_level === "CRITICAL" || c.risk_level === "HIGH");
  } else if (activeFilter === "predictions") {
    displayedCases = displayedCases.filter(
      (c) => (c.top_k_atms && c.top_k_atms.length > 0) || c.predicted_cashout_amount > 0 || c.predicted_area
    );
  } else if (activeFilter === "feasibility") {
    displayedCases = displayedCases.filter(
      (c) =>
        c.police_feasibility?.feasibility_status === "HIGH" ||
        (c.police_feasibility?.time_margin_minutes != null && c.police_feasibility.time_margin_minutes > 10) ||
        (c.priority_score != null && c.priority_score >= 70)
    );
  }

  // Export JSON functionality
  const handleExportCases = () => {
    const payload = {
      export_timestamp: new Date().toISOString(),
      platform: "PROJECT DRISHTI",
      data_mode: "SYNTHETIC DEMONSTRATION DATA",
      filter_applied: activeFilter,
      total_count: displayedCases.length,
      cases: displayedCases,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `DRISHTI_CASES_${activeFilter.toUpperCase()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="overview-container">
      {/* ── 1. COMMAND CENTER HERO (Section 31 & 32) ── */}
      <div
        className="panel-card"
        style={{
          background: "linear-gradient(135deg, rgba(229, 9, 20, 0.08) 0%, rgba(18, 21, 27, 0.95) 100%)",
          border: "1px solid rgba(229, 9, 20, 0.35)",
          padding: "20px 24px",
          marginBottom: "16px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "16px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <span style={{ fontSize: "11px", fontWeight: 800, letterSpacing: "1.5px", color: "var(--red-bright)", textTransform: "uppercase" }}>
              DRISHTI COMMAND CENTER
            </span>
            <span
              className="badge-tag"
              style={{
                fontSize: "10px",
                padding: "2px 8px",
                background: "rgba(245, 165, 36, 0.12)",
                color: "var(--warning)",
                border: "1px solid rgba(245, 165, 36, 0.35)",
              }}
              title="Current platform evaluation uses verified synthetic demonstration benchmark data"
            >
              DEMO MODE · Synthetic Benchmark Data
            </span>
          </div>

          <h1 style={{ fontSize: "22px", fontWeight: 800, letterSpacing: "0.5px", color: "var(--text-primary)", margin: "4px 0" }}>
            PREDICT THE NEXT CASH-OUT BEFORE IT HAPPENS.
          </h1>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)", margin: 0, maxWidth: "720px" }}>
            Predictive cybercrime intelligence for proactive cash-out intervention. Automated analytical decision support for authorized field investigators.
          </p>

          {/* 5D Core Dimensions Preview Strip */}
          <div style={{ display: "flex", gap: "12px", marginTop: "12px", flexWrap: "wrap", fontSize: "11px", color: "var(--text-muted)" }}>
            <span><strong style={{ color: "var(--red-bright)" }}>WHERE:</strong> Cash-Out Terminal</span>
            <span>•</span>
            <span><strong style={{ color: "#FF5252" }}>WHEN:</strong> Withdrawal Window</span>
            <span>•</span>
            <span><strong style={{ color: "var(--warning)" }}>AMOUNT:</strong> Expected Sum</span>
            <span>•</span>
            <span><strong style={{ color: "#60a5fa" }}>WHY:</strong> Model Evidence</span>
            <span>•</span>
            <span><strong style={{ color: "var(--success)" }}>ACTION:</strong> Response Feasibility</span>
          </div>
        </div>

        {/* Global Action Bar */}
        <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
          {onNavigate && (
            <button
              type="button"
              className="btn-primary-action"
              onClick={() => onNavigate("pipeline", "CASE-001-UPI-CRITICAL")}
              title="Launch full 5D Intelligence Pipeline on primary target"
            >
              <span>⚡ 5D PIPELINE</span>
              <span>→</span>
            </button>
          )}

          <button
            type="button"
            className="chip-btn"
            onClick={loadData}
            title="Fetch fresh real-time database telemetry"
          >
            🔄 REFRESH
          </button>

          <button
            type="button"
            className="chip-btn"
            onClick={handleExportCases}
            title="Download active dossiers as JSON"
          >
            📥 EXPORT DOSSIERS
          </button>
        </div>
      </div>

      {error && (
        <div className="panel-card" style={{ borderColor: "var(--risk-high-bd)", background: "var(--risk-high-bg)", color: "var(--risk-high)", marginBottom: "16px" }}>
          <span>⚠️ {error}</span>
          <button onClick={loadData} style={{ marginLeft: "12px", background: "none", border: "none", color: "inherit", textDecoration: "underline", cursor: "pointer" }}>
            Retry
          </button>
        </div>
      )}

      {/* ── 2. QUICK ACTIONS STRIP ── */}
      <div
        className="panel-card"
        style={{
          padding: "10px 16px",
          marginBottom: "16px",
          background: "var(--surface)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "10px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
          <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--red-bright)", letterSpacing: "0.8px" }}>
            QUICK ACTIONS:
          </span>
          <button
            type="button"
            className="chip-btn"
            onClick={() => onNavigate && onNavigate("pipeline", "CASE-001-UPI-CRITICAL")}
            style={{ fontSize: "11px" }}
          >
            ⚡ RUN ANALYSIS
          </button>
          <button
            type="button"
            className={`chip-btn ${activeFilter === "critical_top10" ? "active" : ""}`}
            onClick={() => setActiveFilter("critical_top10")}
            style={{ fontSize: "11px", borderColor: "rgba(229,9,20,0.4)", color: "var(--red-bright)" }}
          >
            🚨 TOP CRITICAL ({criticalCasesCount > 10 ? 10 : criticalCasesCount})
          </button>
          <button
            type="button"
            className="chip-btn"
            onClick={() => onNavigate && onNavigate("pipeline", "CASE-001-UPI-CRITICAL")}
            style={{ fontSize: "11px" }}
          >
            🗺️ VIEW MAP
          </button>
          <button
            type="button"
            className="chip-btn"
            onClick={() => onNavigate && onNavigate("pipeline", "CASE-001-UPI-CRITICAL")}
            style={{ fontSize: "11px" }}
          >
            🕸️ MONEY TRAIL
          </button>
          {onNavigate && (
            <button
              type="button"
              className="chip-btn"
              onClick={() => onNavigate("data-trust")}
              style={{ fontSize: "11px" }}
            >
              🛡️ DATA &amp; TRUST
            </button>
          )}
        </div>

        {/* Live Search Input */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ fontSize: "11.5px", color: "var(--text-muted)" }}>🔍</span>
          <input
            type="text"
            placeholder="Quick search dossiers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              background: "rgba(0,0,0,0.3)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-xs)",
              padding: "4px 8px",
              color: "var(--text-primary)",
              fontSize: "11.5px",
              width: "180px",
            }}
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "11px" }}
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* ── 3. 6 CLICKABLE KPI METRIC CARDS (Section 5) ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
          gap: "10px",
          marginBottom: "16px",
        }}
      >
        <div
          className={`stat-pill ${activeFilter === "all" ? "active" : ""}`}
          onClick={() => setActiveFilter("all")}
          style={{ cursor: "pointer", padding: "10px 14px", display: "flex", flexDirection: "column", gap: "2px" }}
          title="Click to view all cases"
        >
          <span className="stat-pill-label" style={{ fontSize: "10.5px" }}>TOTAL CASES</span>
          <span className="stat-pill-value" style={{ fontSize: "18px" }}>{loading ? "..." : totalCases}</span>
        </div>

        <div
          className={`stat-pill ${activeFilter === "active" ? "active" : ""}`}
          onClick={() => setActiveFilter("active")}
          style={{ cursor: "pointer", padding: "10px 14px", display: "flex", flexDirection: "column", gap: "2px" }}
          title="Click to view active cases"
        >
          <span className="stat-pill-label" style={{ fontSize: "10.5px" }}>ACTIVE CASES</span>
          <span className="stat-pill-value" style={{ fontSize: "18px", color: "#60a5fa" }}>{loading ? "..." : activeCasesCount}</span>
        </div>

        <div
          className={`stat-pill ${activeFilter === "critical_top10" ? "active" : ""}`}
          onClick={() => setActiveFilter("critical_top10")}
          style={{ cursor: "pointer", padding: "10px 14px", display: "flex", flexDirection: "column", gap: "2px", borderColor: "rgba(229,9,20,0.4)" }}
          title="Click to filter Top 10 critical cases sorted by risk"
        >
          <span className="stat-pill-label" style={{ fontSize: "10.5px" }}>CRITICAL (TOP 10)</span>
          <span className="stat-pill-value text-red" style={{ fontSize: "18px" }}>
            {loading ? "..." : (criticalCasesCount > 10 ? 10 : criticalCasesCount)}
          </span>
        </div>

        <div
          className={`stat-pill ${activeFilter === "high_risk" ? "active" : ""}`}
          onClick={() => setActiveFilter("high_risk")}
          style={{ cursor: "pointer", padding: "10px 14px", display: "flex", flexDirection: "column", gap: "2px" }}
          title="Click to view all high-risk syndicates"
        >
          <span className="stat-pill-label" style={{ fontSize: "10.5px" }}>HIGH RISK SYNDICATES</span>
          <span className="stat-pill-value" style={{ fontSize: "18px", color: "var(--warning)" }}>{loading ? "..." : criticalCasesCount}</span>
        </div>

        <div
          className={`stat-pill ${activeFilter === "predictions" ? "active" : ""}`}
          onClick={() => setActiveFilter("predictions")}
          style={{ cursor: "pointer", padding: "10px 14px", display: "flex", flexDirection: "column", gap: "2px" }}
          title="Click to view cases with active 5D predictions"
        >
          <span className="stat-pill-label" style={{ fontSize: "10.5px" }}>PREDICTIONS READY</span>
          <span className="stat-pill-value" style={{ fontSize: "18px", color: "var(--red-bright)" }}>{loading ? "..." : predictedCashouts}</span>
        </div>

        <div
          className={`stat-pill ${activeFilter === "feasibility" ? "active" : ""}`}
          onClick={() => setActiveFilter("feasibility")}
          style={{ cursor: "pointer", padding: "10px 14px", display: "flex", flexDirection: "column", gap: "2px" }}
          title="Click to view cases with high intercept feasibility"
        >
          <span className="stat-pill-label" style={{ fontSize: "10.5px" }}>HIGH FEASIBILITY</span>
          <span className="stat-pill-value" style={{ fontSize: "18px", color: "var(--success)" }}>{loading ? "..." : highFeasibilityCount}</span>
        </div>
      </div>

      {/* ── 4. FEATURED ACTIVE DOSSIER ── */}
      <div className="featured-case-card">
        <div className="featured-content">
          <span className="featured-tag">PRIMARY INVESTIGATION TARGET</span>
          <h2 className="featured-title">Case #CASE-001-UPI-CRITICAL — Rapid Multi-Hop UPI Layering (₹85,000)</h2>
          <p className="featured-desc">
            Organized cyber syndicate funneling victim funds through a 3-hop mule account network toward physical ATM cash-out in Banjara Hills / Hitec City. Early interception window active.
          </p>
        </div>
        <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
          {onNavigate && (
            <button
              className="chip-btn"
              onClick={() => onNavigate("pipeline", "CASE-001-UPI-CRITICAL")}
              style={{ padding: "8px 14px", fontSize: "12px", background: "rgba(229,9,20,0.15)", color: "var(--red-bright)", borderColor: "rgba(229,9,20,0.4)" }}
            >
              ⚡ 5D PIPELINE
            </button>
          )}
          <button
            className="btn-primary-action"
            onClick={() => onSelectCase("CASE-001-UPI-CRITICAL")}
          >
            <span>INVESTIGATE DOSSIER</span>
            <span>→</span>
          </button>
        </div>
      </div>

      {/* ── 5. ACTIVE CASES TABLE WITH FUNCTIONAL FILTER STRIP ── */}
      <div className="panel-card">
        <div className="panel-header" style={{ flexWrap: "wrap", gap: "10px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <h2 className="panel-title">Active Intelligence Dossiers</h2>
            {/* Functional Filter Buttons */}
            <div className="filter-chips-group">
              <button
                type="button"
                className={`chip-btn ${activeFilter === "all" ? "active" : ""}`}
                onClick={() => setActiveFilter("all")}
                style={{ fontSize: "11px", padding: "4px 8px" }}
              >
                ALL CASES ({totalCases})
              </button>

              <button
                type="button"
                className={`chip-btn ${activeFilter === "critical_top10" ? "active" : ""}`}
                onClick={() => setActiveFilter("critical_top10")}
                style={{ fontSize: "11px", padding: "4px 8px", borderColor: "rgba(229,9,20,0.4)", color: activeFilter === "critical_top10" ? "#fff" : "var(--red-bright)" }}
                title="Filter to critical/high risk cases sorted by risk descending, maximum 10"
              >
                🚨 CRITICAL ONLY ({criticalCasesCount > 10 ? 10 : criticalCasesCount})
              </button>

              <button
                type="button"
                className={`chip-btn ${activeFilter === "active" ? "active" : ""}`}
                onClick={() => setActiveFilter("active")}
                style={{ fontSize: "11px", padding: "4px 8px" }}
              >
                ACTIVE ({activeCasesCount})
              </button>

              <button
                type="button"
                className={`chip-btn ${activeFilter === "recent" ? "active" : ""}`}
                onClick={() => setActiveFilter("recent")}
                style={{ fontSize: "11px", padding: "4px 8px" }}
              >
                RECENT
              </button>

              <button
                type="button"
                className={`chip-btn ${activeFilter === "feasibility" ? "active" : ""}`}
                onClick={() => setActiveFilter("feasibility")}
                style={{ fontSize: "11px", padding: "4px 8px" }}
                title="Filter cases with actionable patrol response feasibility"
              >
                FEASIBLE ({highFeasibilityCount})
              </button>
            </div>
          </div>

          <button
            className="btn-table-action"
            onClick={() => onNavigate("cases")}
          >
            Full Case Registry →
          </button>
        </div>

        <div className="table-responsive">
          <table className="drishti-table">
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Fraud Typology</th>
                <th>Loss Amount</th>
                <th>Target Locality</th>
                <th>Risk Tier</th>
                <th>Status</th>
                <th style={{ textAlign: "right" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: "center", padding: "24px", color: "var(--text-muted)" }}>
                    Loading active intelligence cases...
                  </td>
                </tr>
              ) : displayedCases.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: "center", padding: "24px", color: "var(--text-muted)" }}>
                    No investigation dossiers matched the current filter.
                  </td>
                </tr>
              ) : (
                displayedCases.slice(0, 10).map((c) => {
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
                      <td>
                        {c.fraud_type
                          ? c.fraud_type.replace("_", " ").toUpperCase()
                          : "CYBER FRAUD"}
                      </td>
                      <td className="font-mono text-amber">
                        ₹{Number(c.amount || 0).toLocaleString("en-IN")}
                      </td>
                      <td>{c.city || "Hyderabad"}</td>
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

      {/* ── 6. SUBTLE ACTIVE INTELLIGENCE STRIP ── */}
      <div className="panel-card" style={{ padding: "14px 20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px", fontSize: "12px", color: "var(--text-muted)" }}>
          <div>
            <strong style={{ color: "var(--text-secondary)" }}>Tactical Ground Telemetry:</strong> 520 Verified ATMs (Hyderabad Cluster) · 21 Police Patrol Units Active
          </div>
          <div>
            <strong style={{ color: "var(--text-secondary)" }}>Model Coverage:</strong> Conformal 90% Confidence Window · 0.7041 MRR Location Precision
          </div>
        </div>
      </div>
    </div>
  );
}
