import React, { useState, useEffect } from "react";
import { fetchCases } from "../api.js";

const PATROL_UNITS = [
  { id: "BC-01", name: "Blue Colts Unit 01", jurisdiction: "Banjara Hills PS", vehicle: "TVS Apache 200", status: "ON PATROL", officer: "SI R. Sharma" },
  { id: "BC-02", name: "Blue Colts Unit 02", jurisdiction: "Jubilee Hills PS", vehicle: "TVS Apache 200", status: "AVAILABLE", officer: "ASI V. Reddy" },
  { id: "BC-03", name: "Blue Colts Unit 03", jurisdiction: "Madhapur PS", vehicle: "Bajaj Pulsar 220", status: "ON PATROL", officer: "HC K. Rao" },
  { id: "BC-04", name: "Blue Colts Unit 04", jurisdiction: "Cyberabad Central", vehicle: "Mahindra Bolero Interceptor", status: "DISPATCHED", officer: "Insp. M. Kumar" },
  { id: "BC-05", name: "Blue Colts Unit 05", jurisdiction: "Gachibowli PS", vehicle: "TVS Apache 200", status: "AVAILABLE", officer: "SI T. Naidu" },
  { id: "BC-06", name: "Blue Colts Unit 06", jurisdiction: "Kukatpally PS", vehicle: "Bajaj Pulsar 220", status: "ON PATROL", officer: "ASI S. Ali" },
];

export default function FieldOperationsView({ onSelectCase }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [unitStatuses, setUnitStatuses] = useState(
    PATROL_UNITS.reduce((acc, u) => ({ ...acc, [u.id]: u.status }), {})
  );

  useEffect(() => {
    async function loadActionCases() {
      setLoading(true);
      try {
        const data = await fetchCases({ limit: 30 });
        setCases(data.filter((c) => c.status === "ACTION_REQUIRED" || c.status === "FIELD_ACTION" || c.status === "HIGH_PRIORITY"));
      } catch (err) {
        console.error("Failed to load operations cases:", err);
      } finally {
        setLoading(false);
      }
    }
    loadActionCases();
  }, []);

  const toggleUnitStatus = (unitId) => {
    setUnitStatuses((prev) => {
      const current = prev[unitId];
      const next = current === "AVAILABLE" ? "DISPATCHED" : current === "DISPATCHED" ? "ON PATROL" : "AVAILABLE";
      return { ...prev, [unitId]: next };
    });
  };

  return (
    <div className="operations-container">
      <div className="operations-header">
        <div>
          <h1 className="operations-title">FIELD OPERATIONS & BLUE COLTS RAPID DISPATCH</h1>
          <p className="operations-subtitle">
            Law enforcement tactical resource allocation, live interceptor telemetry, and proactive surveillance zones
          </p>
        </div>
        <div className="unit-summary-pill font-mono">
          <span>ACTIVE UNITS: {PATROL_UNITS.length} PATROL VECTORS</span>
        </div>
      </div>

      <div className="operations-grid">
        {/* Tactical Patrol Units Roster */}
        <div className="ops-panel">
          <div className="panel-header-strip">
            <span className="strip-title">🚔 JURISDICTIONAL RESPONSE UNITS</span>
            <span className="strip-pill">BLUE COLTS NETWORK</span>
          </div>

          <div className="patrol-units-list">
            {PATROL_UNITS.map((u) => {
              const st = unitStatuses[u.id];
              return (
                <div key={u.id} className="patrol-unit-card">
                  <div className="unit-card-header">
                    <div className="unit-identity">
                      <span className="unit-name font-bold">{u.name}</span>
                      <span className="unit-jurisdiction font-mono text-muted text-xs">{u.jurisdiction}</span>
                    </div>
                    <span
                      className={`unit-status-tag ${
                        st === "DISPATCHED" ? "status-dispatched" : st === "ON PATROL" ? "status-patrol" : "status-avail"
                      }`}
                    >
                      {st}
                    </span>
                  </div>

                  <div className="unit-card-meta font-mono text-xs">
                    <div>Vehicle: <strong>{u.vehicle}</strong></div>
                    <div>In Charge: <strong>{u.officer}</strong></div>
                  </div>

                  <div className="unit-card-actions">
                    <button
                      className="btn-toggle-unit"
                      onClick={() => toggleUnitStatus(u.id)}
                    >
                      {st === "DISPATCHED" ? "Recall to Patrol" : st === "ON PATROL" ? "Mark Available" : "🚨 Dispatch Unit"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Priority Action Cases Queue */}
        <div className="ops-panel">
          <div className="panel-header-strip">
            <span className="strip-title">🎯 ACTIVE SURVEILLANCE & INTERCEPTION TARGETS</span>
            <span className="strip-pill">HIGH PRIORITY</span>
          </div>

          {loading ? (
            <div className="ops-loading">Loading tactical queues...</div>
          ) : cases.length === 0 ? (
            <div className="ops-empty">
              <span className="empty-icon">✓</span>
              <h4>No Critical Interceptions Pending</h4>
              <p>All active cases are currently monitored or resolved.</p>
            </div>
          ) : (
            <div className="action-targets-list">
              {cases.map((c) => (
                <div
                  key={c.case_id}
                  className="action-target-card"
                  onClick={() => onSelectCase && onSelectCase(c.case_id)}
                >
                  <div className="target-card-top">
                    <div className="target-id-group">
                      <span className="target-id font-mono font-bold">{c.case_id}</span>
                      <span className={`target-risk-pill risk-${c.risk_level?.toLowerCase()}`}>
                        {c.risk_level}
                      </span>
                    </div>
                    <span className="target-status font-mono text-xs">{c.status}</span>
                  </div>

                  <div className="target-details-row font-mono text-xs">
                    <div>ATM Target: <strong className="text-cyan">{c.predicted_atm_id || "Banjara Hills"}</strong></div>
                    <div>Window: <strong className="text-amber">{c.predicted_withdrawal_window || "35m"}</strong></div>
                    <div>At Risk: <strong className="text-emerald">₹{c.predicted_cashout_amount ? Math.round(c.predicted_cashout_amount).toLocaleString("en-IN") : "85,000"}</strong></div>
                  </div>

                  <div className="target-action-row">
                    <button
                      className="btn-target-dossier"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onSelectCase) onSelectCase(c.case_id);
                      }}
                    >
                      Inspect Case Dossier →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
