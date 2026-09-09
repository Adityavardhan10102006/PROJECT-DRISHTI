import React, { useState, useEffect } from "react";
import { fetchCases } from "../api.js";

export default function CasesListView({ onSelectCase }) {
  const [cases, setCases] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadCases = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCases({
        status: statusFilter || undefined,
        risk_level: riskFilter || undefined,
        search: searchQuery || undefined,
        limit: 100,
      });
      setCases(data);
    } catch (err) {
      setError(err.message || "Failed to load cases list");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, [statusFilter, riskFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadCases();
  };

  const getRiskClass = (r) => {
    switch (r?.toUpperCase()) {
      case "CRITICAL":
        return "badge-critical";
      case "HIGH":
        return "badge-high";
      case "MEDIUM":
        return "badge-medium";
      default:
        return "badge-low";
    }
  };

  const getStatusClass = (s) => {
    switch (s?.toUpperCase()) {
      case "ACTION_REQUIRED":
        return "status-action-required";
      case "FIELD_ACTION":
        return "status-field-action";
      case "HIGH_PRIORITY":
        return "status-high-priority";
      case "RESOLVED":
        return "status-resolved";
      case "CLOSED":
        return "status-closed";
      default:
        return "status-new";
    }
  };

  return (
    <div className="cases-view-container">
      <div className="cases-header">
        <div>
          <h1 className="cases-title">CYBERCRIME INVESTIGATION DOSSIERS</h1>
          <p className="cases-subtitle">
            Case registry, priority queuing, and field operation tracking
          </p>
        </div>
        <button className="btn-refresh" onClick={loadCases}>
          🔄 Refresh
        </button>
      </div>

      {/* FILTER CONTROLS */}
      <div className="cases-filter-bar">
        <form onSubmit={handleSearchSubmit} className="search-form">
          <input
            type="text"
            className="search-input"
            placeholder="Search by Case ID, Complaint ID, Area, Investigator..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button type="submit" className="btn-search">
            Search
          </button>
          {searchQuery && (
            <button
              type="button"
              className="btn-clear"
              onClick={() => {
                setSearchQuery("");
                loadCases();
              }}
            >
              Clear
            </button>
          )}
        </form>

        <div className="filter-dropdowns">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="filter-select"
          >
            <option value="">Status: All</option>
            <option value="NEW">New</option>
            <option value="ANALYZING">Analyzing</option>
            <option value="HIGH_PRIORITY">High Priority</option>
            <option value="ACTION_REQUIRED">Action Required</option>
            <option value="FIELD_ACTION">Field Action</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
          </select>

          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="filter-select"
          >
            <option value="">Risk: All</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>
      </div>

      {error && <div className="command-error-banner">⚠️ {error}</div>}

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <span>Loading investigation records...</span>
        </div>
      ) : cases.length === 0 ? (
        <div className="empty-state">No investigation cases match the selected filters.</div>
      ) : (
        <div className="table-responsive">
          <table className="drishti-table">
            <thead>
              <tr>
                <th>CASE ID</th>
                <th>COMPLAINT ID</th>
                <th>FRAUD TYPE</th>
                <th>AMOUNT</th>
                <th>RISK</th>
                <th>PRIORITY</th>
                <th>PREDICTED AREA</th>
                <th>INVESTIGATOR</th>
                <th>STATUS</th>
                <th>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr
                  key={c.case_id}
                  className="clickable-row"
                  onClick={() => onSelectCase(c.case_id)}
                >
                  <td className="font-mono text-cyan">{c.case_id}</td>
                  <td className="font-mono text-muted">{c.complaint_id}</td>
                  <td>
                    <span className="fraud-type-pill font-mono">
                      {c.fraud_type}
                    </span>
                  </td>
                  <td className="font-mono font-bold">
                    ₹{Number(c.amount || 0).toLocaleString("en-IN")}
                  </td>
                  <td>
                    <span className={`badge-pill ${getRiskClass(c.risk_level)}`}>
                      {c.risk_score ? `${c.risk_score}` : "—"} [{c.risk_level}]
                    </span>
                  </td>
                  <td>
                    <span className="priority-value font-mono">
                      {c.priority_score ? c.priority_score.toFixed(1) : "—"}
                    </span>
                  </td>
                  <td className="location-cell">
                    📍 {c.predicted_area || "Hyderabad Area"}
                  </td>
                  <td>
                    <span className="investigator-name">
                      👤 {c.assigned_investigator || "Unassigned"}
                    </span>
                  </td>
                  <td>
                    <span className={`status-pill ${getStatusClass(c.status)}`}>
                      {c.status.replace("_", " ")}
                    </span>
                  </td>
                  <td>
                    <button
                      className="btn-inspect"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectCase(c.case_id);
                      }}
                    >
                      Dossier →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
