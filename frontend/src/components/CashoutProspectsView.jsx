/**
 * src/components/CashoutProspectsView.jsx — Project DRISHTI
 * ==========================================================
 * Candidate Cash-Out Prospects Search & Multi-Factor Priority Ranking.
 *
 * Answers: "Where is this money most likely to be withdrawn?"
 *
 * Features:
 *   - Multi-factor candidate priority score:
 *     Score = 0.35 * P_ML + 0.20 * Distance + 0.15 * TimeMatch + 0.15 * AmountCompat + 0.15 * PoliceFeasibility
 *   - Transparent "WHY THIS ATM?" explainability factors
 *   - Active Case Context switcher
 *   - Interactive ATM Intelligence Drawer
 *   - Seamless handoff to Map and Money Trail
 */

import React, { useState, useEffect } from "react";
import { fetchCandidateProspects, fetchCases } from "../api.js";

export default function CashoutProspectsView({
  onSelectCase,
  onNavigateTab,
  activeCaseId = null,
}) {
  const [selectedCaseId, setSelectedCaseId] = useState(activeCaseId || "DR-2026-1001");
  const [casesList, setCasesList] = useState([]);
  const [amount, setAmount] = useState(85000);
  const [fraudType, setFraudType] = useState("upi_fraud");
  const [victimLat, setVictimLat] = useState(17.4435);
  const [victimLon, setVictimLon] = useState(78.3772);

  const [candidates, setCandidates] = useState([]);
  const [scoringFormula, setScoringFormula] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ATM Intelligence Drawer State
  const [selectedAtm, setSelectedAtm] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [caseNoteAdded, setCaseNoteAdded] = useState(false);

  // Load available cases for context dropdown
  useEffect(() => {
    fetchCases({ limit: 20 })
      .then((cases) => {
        if (cases && cases.length > 0) {
          setCasesList(cases);
          if (!activeCaseId) {
            setSelectedCaseId(cases[0].case_id);
            setAmount(cases[0].amount || 85000);
            setFraudType(cases[0].fraud_type || "upi_fraud");
            setVictimLat(cases[0].victim_lat || 17.4435);
            setVictimLon(cases[0].victim_lon || 78.3772);
          }
        }
      })
      .catch(() => {});
  }, [activeCaseId]);

  // When selectedCaseId changes, update coords and reload candidates
  const handleCaseChange = (cid) => {
    setSelectedCaseId(cid);
    const found = casesList.find((c) => c.case_id === cid);
    if (found) {
      setAmount(found.amount || 50000);
      setFraudType(found.fraud_type || "upi_fraud");
      if (found.victim_lat) setVictimLat(found.victim_lat);
      if (found.victim_lon) setVictimLon(found.victim_lon);
    }
  };

  const loadProspects = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCandidateProspects({
        case_id: selectedCaseId || undefined,
        victim_lat: victimLat,
        victim_lon: victimLon,
        amount: amount,
        fraud_type: fraudType,
        k: 8,
      });
      setCandidates(data.candidates || []);
      setScoringFormula(data.scoring_formula || "");
    } catch (err) {
      setError(err.message || "Failed to load candidate cash-out prospects");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProspects();
  }, [selectedCaseId]);

  const openAtmDrawer = (cand) => {
    setSelectedAtm(cand);
    setDrawerOpen(true);
    setCaseNoteAdded(false);
  };

  const getPriorityBadgeClass = (tier) => {
    switch (tier?.toUpperCase()) {
      case "CRITICAL": return "badge-critical";
      case "HIGH": return "badge-high";
      case "MEDIUM": return "badge-medium";
      default: return "badge-low";
    }
  };

  return (
    <div className="prospects-view-container" style={{ padding: "20px 24px", color: "var(--text-primary)" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: "0 0 6px 0", fontSize: 24, fontWeight: 800, letterSpacing: "-0.5px" }}>
            # CASH-OUT PROSPECTS
          </h1>
          <p style={{ margin: 0, fontSize: 13, color: "var(--text-muted)" }}>
            Forecasting likely ATM cash withdrawal locations with multi-factor priority ranking
          </p>
        </div>

        {/* Responsible AI Badge */}
        <div style={{
          fontSize: 11,
          padding: "5px 12px",
          borderRadius: 4,
          background: "rgba(16, 185, 129, 0.12)",
          border: "1px solid rgba(16, 185, 129, 0.3)",
          color: "#34d399",
          fontWeight: 700,
          maxWidth: 380,
          textAlign: "right",
        }}>
          DECISION SUPPORT ONLY — Requires authorized human supervisor dispatch
        </div>
      </div>

      {/* Investigation Context Selector Card */}
      <div style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "16px 20px",
        marginBottom: 20,
        boxShadow: "0 4px 16px rgba(0, 0, 0, 0.2)",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12, flexWrap: "wrap", gap: 10 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: "var(--text-muted)" }}>
              INVESTIGATION CONTEXT:
            </span>
            <select
              value={selectedCaseId}
              onChange={(e) => handleCaseChange(e.target.value)}
              style={{
                background: "var(--bg-primary)",
                border: "1px solid var(--border)",
                color: "var(--text-primary)",
                borderRadius: 4,
                padding: "6px 12px",
                fontSize: 13,
                fontWeight: 700,
              }}
            >
              {casesList.map((c) => (
                <option key={c.case_id} value={c.case_id}>
                  {c.case_id} — {c.title || c.fraud_type} (₹{c.amount?.toLocaleString()})
                </option>
              ))}
              <option value="CUSTOM">Custom Incident Coordinates</option>
            </select>
          </div>

          <div style={{ display: "flex", gap: 14, fontSize: 12, color: "var(--text-secondary)" }}>
            <span>Target Amount: <strong>₹{amount?.toLocaleString()}</strong></span>
            <span>Origin: <strong>{victimLat.toFixed(4)}, {victimLon.toFixed(4)}</strong></span>
            <span>Fraud Type: <strong>{fraudType.replace("_", " ").toUpperCase()}</strong></span>
          </div>

          <button
            type="button"
            onClick={loadProspects}
            disabled={loading}
            style={{
              background: "var(--accent, #3b82f6)",
              border: "none",
              borderRadius: 4,
              padding: "6px 16px",
              color: "#fff",
              fontSize: 12,
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            {loading ? "Re-ranking..." : "Refresh Prospects ↻"}
          </button>
        </div>

        {/* Transparent Formula Bar */}
        <div style={{
          fontSize: 11,
          background: "rgba(0, 0, 0, 0.25)",
          border: "1px solid rgba(255, 255, 255, 0.06)",
          borderRadius: 4,
          padding: "6px 12px",
          color: "var(--text-muted)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 6,
        }}>
          <div>
            <strong style={{ color: "#93c5fd" }}>Priority Scoring Formula:</strong>{" "}
            <code>Score = 0.35·P_ML + 0.20·Distance + 0.15·TimeMatch + 0.15·AmountCompat + 0.15·PoliceFeasibility</code>
          </div>
          <span style={{ color: "#34d399", fontWeight: 700 }}>
            Calibrated XGBoost + Spatial Haversine
          </span>
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div style={{ padding: "40px 0", textAlign: "center", color: "var(--text-muted)" }}>
          <div style={{ fontSize: 28, marginBottom: 8 }}>🛰️</div>
          Evaluating spatial candidate density and police feasibility...
        </div>
      )}

      {error && (
        <div style={{
          background: "rgba(239, 68, 68, 0.12)",
          border: "1px solid #ef4444",
          color: "#f87171",
          borderRadius: 8,
          padding: "12px 16px",
          marginBottom: 16,
        }}>
          {error}
        </div>
      )}

      {/* Candidate Cards Grid */}
      {!loading && candidates.length > 0 && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))",
          gap: 16,
        }}>
          {candidates.map((cand) => {
            const scorePct = Math.round((cand.candidate_priority_score || 0.5) * 100);
            const mlPct = Math.round((cand.ml_probability || 0.5) * 100);

            return (
              <div
                key={cand.atm_id}
                style={{
                  background: "var(--surface)",
                  border: `1px solid ${cand.rank === 1 ? "rgba(59, 130, 246, 0.6)" : "var(--border)"}`,
                  borderRadius: 8,
                  padding: "18px 20px",
                  position: "relative",
                  boxShadow: cand.rank === 1 ? "0 4px 20px rgba(59, 130, 246, 0.15)" : "0 2px 10px rgba(0,0,0,0.15)",
                }}
              >
                {/* Candidate Rank Badge */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{
                      fontSize: 12,
                      fontWeight: 900,
                      background: cand.rank === 1 ? "var(--accent, #3b82f6)" : "rgba(255, 255, 255, 0.1)",
                      color: "#fff",
                      padding: "3px 8px",
                      borderRadius: 4,
                      letterSpacing: "0.5px",
                    }}>
                      CANDIDATE #{cand.rank}
                    </span>
                    <span style={{ fontSize: 15, fontWeight: 800, color: "var(--text-primary)" }}>
                      {cand.atm_id}
                    </span>
                  </div>

                  <span className={`badge ${getPriorityBadgeClass(cand.priority_tier)}`} style={{ fontSize: 11, padding: "3px 8px" }}>
                    {cand.priority_tier} PRIORITY
                  </span>
                </div>

                {/* ATM Name & Bank */}
                <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>
                  {cand.atm_name}
                </div>
                <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 12 }}>
                  🏦 {cand.bank} Terminal | 📍 {cand.latitude.toFixed(4)}, {cand.longitude.toFixed(4)}
                </div>

                {/* Core Metrics Grid */}
                <div style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 8,
                  background: "rgba(0, 0, 0, 0.2)",
                  padding: "10px 12px",
                  borderRadius: 6,
                  marginBottom: 12,
                  fontSize: 12,
                }}>
                  <div>
                    <span style={{ color: "var(--text-muted)", display: "block", fontSize: 10 }}>ML PROBABILITY</span>
                    <strong style={{ color: "#60a5fa", fontSize: 15 }}>{mlPct}%</strong>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)", display: "block", fontSize: 10 }}>DISTANCE FROM ORIGIN</span>
                    <strong style={{ color: "var(--text-primary)", fontSize: 15 }}>{cand.distance_km} km</strong>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)", display: "block", fontSize: 10 }}>TIME MATCH</span>
                    <strong style={{ color: cand.time_match === "HIGH" ? "#34d399" : "#fbbf24" }}>
                      {cand.time_match}
                    </strong>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)", display: "block", fontSize: 10 }}>AMOUNT COMPATIBILITY</span>
                    <strong style={{ color: cand.amount_compatibility === "HIGH" ? "#34d399" : "#fbbf24" }}>
                      {cand.amount_compatibility}
                    </strong>
                  </div>
                </div>

                {/* Nearest Response Unit */}
                <div style={{
                  fontSize: 11,
                  background: "rgba(16, 185, 129, 0.08)",
                  border: "1px solid rgba(16, 185, 129, 0.25)",
                  borderRadius: 4,
                  padding: "6px 10px",
                  marginBottom: 12,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}>
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Response Unit: </span>
                    <strong style={{ color: "#34d399" }}>{cand.nearest_police_unit?.name}</strong>
                  </div>
                  <span style={{ fontWeight: 800, color: "#6ee7b7" }}>
                    ~{cand.nearest_police_unit?.eta_minutes}m ETA
                  </span>
                </div>

                {/* "WHY THIS ATM?" Factor Breakdown */}
                <div style={{
                  background: "rgba(30, 41, 59, 0.45)",
                  borderRadius: 4,
                  padding: "8px 10px",
                  marginBottom: 14,
                  fontSize: 11,
                }}>
                  <div style={{ fontWeight: 700, color: "#93c5fd", marginBottom: 4 }}>
                    WHY THIS ATM?
                  </div>
                  {(cand.why_factors || []).slice(0, 4).map((f, i) => (
                    <div key={i} style={{ color: "var(--text-secondary)", marginBottom: 2 }}>
                      {f}
                    </div>
                  ))}
                </div>

                {/* Action Buttons */}
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  <button
                    type="button"
                    onClick={() => onNavigateTab && onNavigateTab("command-center")}
                    style={{
                      flex: 1,
                      background: "rgba(59, 130, 246, 0.15)",
                      border: "1px solid rgba(59, 130, 246, 0.4)",
                      color: "#93c5fd",
                      borderRadius: 4,
                      padding: "6px 8px",
                      fontSize: 11,
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    View on Map 🗺️
                  </button>
                  <button
                    type="button"
                    onClick={() => onNavigateTab && onNavigateTab("money-trail")}
                    style={{
                      flex: 1,
                      background: "rgba(255, 255, 255, 0.05)",
                      border: "1px solid var(--border)",
                      color: "var(--text-secondary)",
                      borderRadius: 4,
                      padding: "6px 8px",
                      fontSize: 11,
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    Trace Flow ➔
                  </button>
                  <button
                    type="button"
                    onClick={() => openAtmDrawer(cand)}
                    style={{
                      background: "var(--accent, #3b82f6)",
                      border: "none",
                      color: "#fff",
                      borderRadius: 4,
                      padding: "6px 12px",
                      fontSize: 11,
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    ATM Intelligence
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Slide-in ATM Intelligence Drawer */}
      {drawerOpen && selectedAtm && (
        <div style={{
          position: "fixed",
          top: 0,
          right: 0,
          width: "420px",
          maxWidth: "90vw",
          height: "100vh",
          background: "var(--bg-secondary, #0f172a)",
          borderLeft: "1px solid var(--border)",
          boxShadow: "-10px 0 30px rgba(0, 0, 0, 0.7)",
          zIndex: 1000,
          padding: "24px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          overflowY: "auto",
        }}>
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <span style={{ fontSize: 11, fontWeight: 800, color: "#93c5fd", letterSpacing: "1px" }}>
                ATM INTELLIGENCE DOSSIER
              </span>
              <button
                type="button"
                onClick={() => setDrawerOpen(false)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-muted)",
                  fontSize: 18,
                  cursor: "pointer",
                }}
              >
                ✕
              </button>
            </div>

            <h2 style={{ fontSize: 18, fontWeight: 800, color: "var(--text-primary)", margin: "0 0 4px 0" }}>
              {selectedAtm.atm_name}
            </h2>
            <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>
              Terminal ID: {selectedAtm.atm_id} | Bank: {selectedAtm.bank}
            </div>

            {/* Tactical Metrics Table */}
            <div style={{
              background: "rgba(0, 0, 0, 0.3)",
              border: "1px solid var(--border)",
              borderRadius: 6,
              padding: "12px",
              marginBottom: 16,
              fontSize: 12,
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                <span style={{ color: "var(--text-muted)" }}>ML Withdrawal Probability</span>
                <strong style={{ color: "#60a5fa" }}>{(selectedAtm.ml_probability * 100).toFixed(1)}%</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                <span style={{ color: "var(--text-muted)" }}>Composite Priority Score</span>
                <strong style={{ color: "#34d399" }}>{(selectedAtm.candidate_priority_score * 100).toFixed(1)} / 100</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                <span style={{ color: "var(--text-muted)" }}>Distance from Origin</span>
                <span>{selectedAtm.distance_km} km</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                <span style={{ color: "var(--text-muted)" }}>Historical Cluster Activity</span>
                <span>{selectedAtm.historical_activity}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0" }}>
                <span style={{ color: "var(--text-muted)" }}>Assigned Patrol Unit</span>
                <span style={{ color: "#6ee7b7" }}>{selectedAtm.nearest_police_unit?.name}</span>
              </div>
            </div>

            {/* Why This ATM Detail */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-secondary)", marginBottom: 6 }}>
                Investigative Rationale:
              </div>
              <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: "var(--text-muted)", lineHeight: 1.6 }}>
                {selectedAtm.why_factors?.map((wf, idx) => (
                  <li key={idx}>{wf}</li>
                ))}
              </ul>
            </div>

            {/* Prototype Data Notice */}
            <div style={{
              background: "rgba(59, 130, 246, 0.08)",
              border: "1px solid rgba(59, 130, 246, 0.25)",
              borderRadius: 4,
              padding: "8px 12px",
              fontSize: 11,
              color: "#93c5fd",
              marginBottom: 16,
            }}>
              ℹ️ <strong>Prototype Geospatial Catalog:</strong> ATM coordinates and past withdrawal volumes reflect curated demonstration data. Does not tap confidential National Financial Switch feeds.
            </div>

            {caseNoteAdded && (
              <div style={{
                background: "rgba(16, 185, 129, 0.15)",
                border: "1px solid #10b981",
                color: "#6ee7b7",
                padding: "8px 12px",
                borderRadius: 4,
                fontSize: 12,
                marginBottom: 12,
              }}>
                ✓ ATM {selectedAtm.atm_id} added to investigation case docket.
              </div>
            )}
          </div>

          {/* Action Buttons in Drawer */}
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 16 }}>
            <button
              type="button"
              onClick={() => {
                setCaseNoteAdded(true);
                setTimeout(() => setCaseNoteAdded(false), 3000);
              }}
              style={{
                background: "var(--accent, #3b82f6)",
                border: "none",
                borderRadius: 6,
                padding: "10px",
                color: "#fff",
                fontWeight: 700,
                fontSize: 13,
                cursor: "pointer",
              }}
            >
              Add to Active Case Dossier
            </button>

            <button
              type="button"
              onClick={() => {
                setDrawerOpen(false);
                onNavigateTab && onNavigateTab("command-center");
              }}
              style={{
                background: "rgba(255, 255, 255, 0.06)",
                border: "1px solid var(--border)",
                borderRadius: 6,
                padding: "8px",
                color: "var(--text-primary)",
                fontSize: 12,
                cursor: "pointer",
              }}
            >
              Center on Map
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
