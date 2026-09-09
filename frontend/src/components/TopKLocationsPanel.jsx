/**
 * src/components/TopKLocationsPanel.jsx — Project DRISHTI
 * Ranked Top-K Candidate Cash-Out Locations Panel.
 *
 * Provides law enforcement with:
 *   - Ranked ATM clusters (#1 Primary, #2 Secondary, #3 Alternative)
 *   - Calibrated ML withdrawal probabilities from XGBoost Location Predictor
 *   - ATM density and distance from victim origin
 *   - Concrete evidence summary for tactical decision making
 *   - Interactive "Focus on Map" triggers
 */

export default function TopKLocationsPanel({ locations, activeRank, onSelectLocation }) {
  if (!locations || locations.length === 0) {
    return (
      <div className="empty-locations-state">
        <span className="empty-icon">📍</span>
        <div className="empty-title">No Candidate Hotspots</div>
        <div className="empty-desc">
          Coordinates required to compute ML candidate ATM ranking.
        </div>
      </div>
    );
  }

  return (
    <div className="top-k-container">
      <div className="top-k-header">
        <div className="top-k-title">
          <span className="icon">🎯</span> Ranked Withdrawal Candidates ({locations.length})
        </div>
        <span className="top-k-hint">XGBoost ML Ranker · Calibrated Probabilities</span>
      </div>

      <div className="top-k-cards-grid">
        {locations.map((loc, idx) => {
          const rank = loc.rank || idx + 1;
          const isPrimary = rank === 1;
          const isSelected = activeRank === rank;
          const prob = Math.round((loc.ranking_probability || loc.probability || loc.confidence || 0.5) * 100);
          const method = loc.prediction_source === "ml_xgboost_ranker" ? "Calibrated ML" : "Heuristic Ranking";

          return (
            <div
              key={idx}
              className={`candidate-card ${isPrimary ? "candidate-primary" : ""} ${
                isSelected ? "candidate-selected" : ""
              }`}
              onClick={() => onSelectLocation?.(loc)}
            >
              {/* Top Row: Rank Badge + Priority Tag */}
              <div className="cand-top-row">
                <div className="cand-rank-group">
                  <span className={`cand-rank-badge rank-${rank}`}>
                    #{rank}
                  </span>
                  <span className="cand-type-tag">
                    {isPrimary ? "PRIMARY TARGET" : `ALTERNATIVE #${rank}`}
                  </span>
                </div>
                {loc.interception_priority && (
                  <span className="cand-priority-pill">
                    Priority {loc.interception_priority}/100
                  </span>
                )}
              </div>

              {/* Candidate Name & Landmark */}
              <div className="cand-name">
                {loc.location_name || `Cluster #${loc.cluster_id || rank}`}
              </div>

              {/* Spatial Metadata */}
              <div className="cand-meta-grid">
                <div className="cand-meta-item">
                  <span className="meta-lbl">ATMs in Cluster</span>
                  <span className="meta-val">{loc.atm_count} active</span>
                </div>
                <div className="cand-meta-item">
                  <span className="meta-lbl">Perimeter Radius</span>
                  <span className="meta-val">{loc.radius_km ? `${loc.radius_km.toFixed(2)} km` : "0.45 km"}</span>
                </div>
                {loc.distance_km !== undefined && (
                  <div className="cand-meta-item">
                    <span className="meta-lbl">Victim Distance</span>
                    <span className="meta-val">{loc.distance_km} km</span>
                  </div>
                )}
                {loc.feasibility?.eta_minutes && (
                  <div className="cand-meta-item">
                    <span className="meta-lbl">Police ETA</span>
                    <span className="meta-val text-green">{loc.feasibility.eta_minutes}m</span>
                  </div>
                )}
              </div>

              {/* Withdrawal Confidence Bar */}
              <div className="cand-confidence-section">
                <div className="conf-bar-labels">
                  <span className="conf-title">Calibrated Probability ({method})</span>
                  <span className="conf-percentage">{prob}%</span>
                </div>
                <div className="conf-track">
                  <div
                    className={`conf-fill ${isPrimary ? "fill-primary" : "fill-secondary"}`}
                    style={{ width: `${prob}%` }}
                  />
                </div>
              </div>

              {/* Tactical Evidence */}
              {loc.reason && (
                <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "6px", fontStyle: "italic", lineHeight: 1.3 }}>
                  Evidence: {loc.reason}
                </div>
              )}

              {/* Action Button */}
              <button
                type="button"
                className="cand-focus-btn"
                style={{ marginTop: "8px" }}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectLocation?.(loc);
                }}
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="m14.83 9.17 4.24-4.24"/><path d="m14.83 14.83 4.24 4.24"/><path d="m9.17 14.83-4.24 4.24"/>
                </svg>
                Focus on Map
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
