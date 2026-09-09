import React, { useState, useEffect } from "react";
import { fetchAuditLogs } from "../api.js";

export default function AuditLogView() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [userFilter, setUserFilter] = useState("");
  const [actionFilter, setActionFilter] = useState("");

  const loadLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAuditLogs({
        user: userFilter || undefined,
        action: actionFilter || undefined,
        limit: 100,
      });
      setLogs(data);
    } catch (err) {
      setError(err.message || "Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [userFilter, actionFilter]);

  return (
    <div className="audit-view-container">
      <div className="audit-header">
        <div>
          <h1 className="audit-title">SECURITY & INVESTIGATION AUDIT LOGS</h1>
          <p className="audit-subtitle">
            Immutable system and user action register for legal compliance and chain of custody
          </p>
        </div>
        <button onClick={loadLogs} className="btn-refresh">
          🔄 Refresh Logs
        </button>
      </div>

      {/* FILTER BAR */}
      <div className="audit-filter-bar">
        <div className="filter-group">
          <label>Filter by Action:</label>
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="filter-select"
          >
            <option value="">All Actions</option>
            <option value="LOGIN">LOGIN</option>
            <option value="CASE_CREATED">CASE CREATED</option>
            <option value="CASE_ASSIGNED">CASE ASSIGNED</option>
            <option value="STATUS_CHANGED">STATUS CHANGED</option>
            <option value="OUTCOME_RECORDED">OUTCOME RECORDED</option>
            <option value="MODEL_EVALUATED">MODEL EVALUATED</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Filter by User:</label>
          <input
            type="text"
            placeholder="Username..."
            value={userFilter}
            onChange={(e) => setUserFilter(e.target.value)}
            className="search-input"
          />
        </div>
      </div>

      {error && <div className="command-error-banner">⚠️ {error}</div>}

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <span>Fetching audit events...</span>
        </div>
      ) : logs.length === 0 ? (
        <div className="empty-state">No audit log records match the query.</div>
      ) : (
        <div className="table-responsive">
          <table className="drishti-table font-mono">
            <thead>
              <tr>
                <th>TIMESTAMP (UTC)</th>
                <th>USER / PRINCIPAL</th>
                <th>ACTION</th>
                <th>CASE ID</th>
                <th>RESULT</th>
                <th>EVENT DETAILS</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td className="text-muted">
                    {log.timestamp ? new Date(log.timestamp).toLocaleString() : "N/A"}
                  </td>
                  <td className="text-cyan">👤 {log.user}</td>
                  <td>
                    <span className="action-tag">{log.action}</span>
                  </td>
                  <td>{log.case_id ? <strong>{log.case_id}</strong> : "—"}</td>
                  <td>
                    <span
                      className={`result-tag ${
                        log.result === "SUCCESS" ? "text-emerald" : "text-red"
                      }`}
                    >
                      {log.result}
                    </span>
                  </td>
                  <td className="details-cell">
                    {log.details ? JSON.stringify(log.details) : "—"}
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
