import React, { useState, useEffect } from "react";
import { fetchCases, fetchCaseTimeline } from "../api.js";

export default function TimelineView({ selectedCaseId, onSelectCase }) {
  const [cases, setCases] = useState([]);
  const [activeCaseId, setActiveCaseId] = useState(selectedCaseId || "");
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadCasesList() {
      try {
        const cList = await fetchCases({ limit: 50 });
        setCases(cList);
        if (!activeCaseId && cList.length > 0) {
          setActiveCaseId(cList[0].case_id);
        }
      } catch (err) {
        console.error("Failed to load cases in timeline view:", err);
      }
    }
    loadCasesList();
  }, []);

  useEffect(() => {
    if (!activeCaseId) return;
    async function loadTimeline() {
      setLoading(true);
      setError(null);
      try {
        const t = await fetchCaseTimeline(activeCaseId);
        setEvents(t);
      } catch (err) {
        setError(err.message || "Failed to load timeline events");
      } finally {
        setLoading(false);
      }
    }
    loadTimeline();
  }, [activeCaseId]);

  const getEventIcon = (type) => {
    switch (type) {
      case "COMPLAINT_RECEIVED":
        return "📥";
      case "COMPLAINT_ANALYZED":
        return "🔍";
      case "MONEY_TRAIL_RECONSTRUCTED":
        return "🕸️";
      case "RISK_PREDICTED":
        return "⚡";
      case "CASHOUT_LOCATION_PREDICTED":
        return "📍";
      case "POLICE_FEASIBILITY_EVALUATED":
        return "🚔";
      case "ALERT_GENERATED":
        return "🚨";
      case "FIELD_ACTION":
        return "🛡️";
      case "ACTUAL_OUTCOME":
        return "🎯";
      case "PREDICTION_EVALUATED":
        return "📊";
      case "STATUS_CHANGED":
        return "🔄";
      case "CASE_ASSIGNED":
        return "👤";
      default:
        return "⏱️";
    }
  };

  return (
    <div className="timeline-view-container">
      <div className="timeline-header">
        <div>
          <h1 className="timeline-title">INVESTIGATION EVENT TIMELINES</h1>
          <p className="timeline-subtitle">
            Auditable, chronological sequence of investigative milestones and model predictions
          </p>
        </div>

        <div className="case-selector-group">
          <label>Select Case:</label>
          <select
            value={activeCaseId}
            onChange={(e) => setActiveCaseId(e.target.value)}
            className="filter-select font-mono"
          >
            {cases.map((c) => (
              <option key={c.case_id} value={c.case_id}>
                {c.case_id} — {c.predicted_area || c.fraud_type} ({c.status})
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <div className="command-error-banner">⚠️ {error}</div>}

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <span>Loading timeline events...</span>
        </div>
      ) : events.length === 0 ? (
        <div className="empty-state">No events recorded for Case {activeCaseId}.</div>
      ) : (
        <div className="timeline-stepper">
          {events.map((ev, index) => (
            <div key={ev.id || index} className="stepper-item">
              <div className="stepper-marker">
                <span className="stepper-icon">{getEventIcon(ev.event_type)}</span>
                {index < events.length - 1 && <div className="stepper-line"></div>}
              </div>

              <div className="stepper-card">
                <div className="stepper-header">
                  <span className="stepper-type font-mono">{ev.event_type}</span>
                  <span className="stepper-time font-mono">
                    {ev.timestamp ? new Date(ev.timestamp).toLocaleString() : "N/A"}
                  </span>
                  <span className="stepper-user font-mono">by {ev.user}</span>
                </div>
                <div className="stepper-body">{ev.description}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
