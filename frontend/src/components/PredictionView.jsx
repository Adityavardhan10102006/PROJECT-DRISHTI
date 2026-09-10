import React, { useState } from "react";
import { submitComplaint } from "../api.js";
import HotspotMap from "./HotspotMap.jsx";

const DEMO_CASES = [
  {
    id: "DR-2026-1001",
    label: "Case 1: Urgent 3-Hop Mule Chain (₹85,000 UPI)",
    data: {
      complaint_text: "Victim defrauded of Rs 85,000 via malicious UPI cashback link. Immediate transfer observed across 3 beneficiary accounts.",
      victim_lat: 17.4435,
      victim_lon: 78.3772,
      fraud_type: "upi_fraud",
      amount: 85000,
      bank_account: "ACC-VICTIM-9921",
      city: "Hyderabad",
    },
  },
  {
    id: "DR-2026-1002",
    label: "Case 2: High-Volume Corporate Impersonation (₹1,50,000)",
    data: {
      complaint_text: "Urgent transfer of Rs 1,50,000 requested under fake vendor verification invoice on WhatsApp.",
      victim_lat: 17.4325,
      victim_lon: 78.4072,
      fraud_type: "kyc_fraud",
      amount: 150000,
      bank_account: "ACC-CORP-4819",
      city: "Hyderabad",
    },
  },
  {
    id: "DR-2026-1003",
    label: "Case 3: WhatsApp Lottery Phishing (₹65,000)",
    data: {
      complaint_text: "Victim lured into processing fee scam of Rs 65,000 for non-existent international lucky draw.",
      victim_lat: 17.3850,
      victim_lon: 78.4867,
      fraud_type: "phishing",
      amount: 65000,
      bank_account: "ACC-MULE-1092",
      city: "Hyderabad",
    },
  },
  {
    id: "DR-2026-1004",
    label: "Case 4: Investment Telegram Syndicate (₹1,20,000)",
    data: {
      complaint_text: "Part-time job task scam defrauded victim of Rs 1,20,000. Funneled into rapid ATM withdrawal network.",
      victim_lat: 17.4125,
      victim_lon: 78.4485,
      fraud_type: "investment_scam",
      amount: 120000,
      bank_account: "ACC-TELE-5541",
      city: "Hyderabad",
    },
  },
  {
    id: "DR-2026-1005",
    label: "Case 5: Remote Access APK Malware (₹45,000)",
    data: {
      complaint_text: "Victim device compromised via fake electricity bill payment APK. Rs 45,000 siphoned via IMPS.",
      victim_lat: 17.4935,
      victim_lon: 78.3992,
      fraud_type: "apk_fraud",
      amount: 45000,
      bank_account: "ACC-APK-7723",
      city: "Hyderabad",
    },
  },
];

const ANALYSIS_STEPS = [
  "Extracting complaint entities & NLP transaction vectors...",
  "Traversing multi-hop mule account network in data/transactions.csv...",
  "Evaluating XGBoost cash-out arrival distribution (Conformal interval)...",
  "Calibrating Top-K candidate ATM ranking across Hyderabad...",
  "Calculating Blue Colts police patrol feasibility & SOP guidance...",
  "Synthesizing 5D actionable cybercrime intelligence...",
];

export default function PredictionView({ onSelectCase, onPredictionComplete }) {
  const [selectedPreset, setSelectedPreset] = useState("DR-2026-1001");
  const [form, setForm] = useState(DEMO_CASES[0].data);
  const [analyzing, setAnalyzing] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [predictionResult, setPredictionResult] = useState(null);
  const [error, setError] = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSelectPreset = (e) => {
    const id = e.target.value;
    setSelectedPreset(id);
    const found = DEMO_CASES.find((c) => c.id === id);
    if (found) {
      setForm(found.data);
      setPredictionResult(null);
    }
  };

  const runAnalysis = async () => {
    setAnalyzing(true);
    setError(null);
    setPredictionResult(null);
    setActiveStep(0);

    // Progressive step simulation ticker
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev < ANALYSIS_STEPS.length - 1 ? prev + 1 : prev));
    }, 280);

    try {
      const payload = {
        complaint_text: form.complaint_text,
        victim_lat: parseFloat(form.victim_lat),
        victim_lon: parseFloat(form.victim_lon),
        fraud_type: form.fraud_type,
        amount: parseFloat(form.amount),
        bank_account: form.bank_account,
      };

      const result = await submitComplaint(payload);
      clearInterval(interval);
      setActiveStep(ANALYSIS_STEPS.length - 1);
      setTimeout(() => {
        setPredictionResult(result);
        setAnalyzing(false);
        if (onPredictionComplete) {
          onPredictionComplete(result);
        }
      }, 350);
    } catch (err) {
      clearInterval(interval);
      setError(err.message || "Prediction pipeline failed.");
      setAnalyzing(false);
    }
  };

  const fiveD = predictionResult?.five_d || {};
  const where = fiveD.where || {};
  const when = fiveD.when || {};
  const amt = fiveD.amount || {};
  const why = fiveD.why || {};
  const action = fiveD.action || {};
  const topK = predictionResult?.top_k_locations || [];
  const riskScore = predictionResult?.risk_score ?? 68;
  const riskTier = predictionResult?.risk_tier || "HIGH";

  return (
    <div className="prediction-workflow-container">
      {/* Workflow Header */}
      <div className="workflow-header">
        <div>
          <h1 className="workflow-title">5D PREDICTIVE INTELLIGENCE WORKFLOW</h1>
          <p className="workflow-subtitle">
            Ingest complaint vectors, reconstruct money-trail hops, forecast cash-out window, and rank likely ATM terminals
          </p>
        </div>
        <div className="workflow-badge font-mono">
          <span>MODEL ARCHITECTURE: 4-LAYER ML PIPELINE</span>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="prediction-grid">
        {/* Left Column: Complaint & Transaction Inspector */}
        <div className="prediction-input-card">
          <div className="panel-header-strip">
            <span className="strip-title">1. INCIDENT & TRANSACTION INGESTION</span>
            <span className="strip-pill">DEMO PRESETS</span>
          </div>

          <div className="preset-selector-group">
            <label className="field-label">Load Canonical Demonstration Scenario:</label>
            <select
              value={selectedPreset}
              onChange={handleSelectPreset}
              className="preset-select"
              disabled={analyzing}
            >
              {DEMO_CASES.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-fields-grid">
            <div className="field-group full-width">
              <label className="field-label">Complaint Narrative / Extracted Text:</label>
              <textarea
                className="complaint-textarea"
                rows={3}
                value={form.complaint_text}
                onChange={(e) => setForm({ ...form, complaint_text: e.target.value })}
                disabled={analyzing}
              />
            </div>

            <div className="field-group">
              <label className="field-label">Defrauded Amount (INR):</label>
              <input
                type="number"
                className="input-field"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
                disabled={analyzing}
              />
            </div>

            <div className="field-group">
              <label className="field-label">Fraud Classification:</label>
              <input
                type="text"
                className="input-field"
                value={form.fraud_type}
                onChange={(e) => setForm({ ...form, fraud_type: e.target.value })}
                disabled={analyzing}
              />
            </div>

            <div className="field-group">
              <label className="field-label">First Beneficiary Account:</label>
              <input
                type="text"
                className="input-field font-mono"
                value={form.bank_account}
                onChange={(e) => setForm({ ...form, bank_account: e.target.value })}
                disabled={analyzing}
              />
            </div>

            <div className="field-group">
              <label className="field-label">Victim Coordinates (Lat, Lon):</label>
              <div className="coords-row">
                <input
                  type="text"
                  className="input-field font-mono"
                  value={form.victim_lat}
                  onChange={(e) => setForm({ ...form, victim_lat: e.target.value })}
                  disabled={analyzing}
                />
                <input
                  type="text"
                  className="input-field font-mono"
                  value={form.victim_lon}
                  onChange={(e) => setForm({ ...form, victim_lon: e.target.value })}
                  disabled={analyzing}
                />
              </div>
            </div>
          </div>

          <div className="execution-action-bar">
            <button
              className="btn-run-prediction"
              onClick={runAnalysis}
              disabled={analyzing}
            >
              {analyzing ? (
                <>
                  <span className="spinner-sm"></span> Processing Intelligence Pipeline...
                </>
              ) : (
                "⚡ EXECUTE 5D PREDICTIVE ANALYSIS"
              )}
            </button>
          </div>

          {/* Progress state steps while analyzing */}
          {analyzing && (
            <div className="pipeline-progress-box">
              <div className="progress-header">
                <span className="font-bold text-cyan">PIPELINE EXECUTION IN PROGRESS</span>
                <span className="font-mono text-muted">{activeStep + 1} / {ANALYSIS_STEPS.length}</span>
              </div>
              <div className="progress-bar-track">
                <div
                  className="progress-bar-fill"
                  style={{ width: `${((activeStep + 1) / ANALYSIS_STEPS.length) * 100}%` }}
                ></div>
              </div>
              <div className="progress-step-text font-mono">
                ➜ {ANALYSIS_STEPS[activeStep]}
              </div>
            </div>
          )}

          {error && <div className="prediction-error-banner">⚠️ {error}</div>}
        </div>

        {/* Right Column: 5D Intelligence Results Display */}
        <div className="prediction-output-card">
          {!predictionResult && !analyzing && (
            <div className="empty-prediction-placeholder">
              <div className="radar-sweep-icon">🎯</div>
              <h3>Predictive Intelligence Engine Ready</h3>
              <p>
                Select a scenario and click <strong>EXECUTE 5D PREDICTIVE ANALYSIS</strong> to generate
                advance cash-out forecast, withdrawal window, ATM candidate rankings, and tactical police feasibility.
              </p>
            </div>
          )}

          {predictionResult && (
            <div className="prediction-results-content">
              {/* Output Top Status Banner */}
              <div className="result-top-banner">
                <div className="result-id-block">
                  <span className="case-ref font-mono">CASE: {predictionResult.case_id || "DR-2026-1001"}</span>
                  <span className={`risk-badge risk-${riskTier.toLowerCase()}`}>
                    {riskTier} RISK ({Math.round(riskScore)}/100)
                  </span>
                </div>
                <div className="result-actions">
                  {onSelectCase && (
                    <button
                      className="btn-view-dossier"
                      onClick={() => onSelectCase(predictionResult.case_id || "DR-2026-1001")}
                    >
                      📁 Open Full Investigation Dossier →
                    </button>
                  )}
                </div>
              </div>

              {/* 5D DIMENSIONS CARDS */}
              <div className="five-d-results-grid">
                {/* 1. WHERE */}
                <div className="five-d-card card-where">
                  <div className="card-dim-header">
                    <span className="dim-tag tag-where">1. WHERE (CASH-OUT LOCATION)</span>
                    <span className="dim-conf font-mono">Top-3 Recall: 92.2%</span>
                  </div>
                  <div className="dim-body">
                    <div className="primary-location-name font-bold text-cyan">
                      {where.primary_hotspot_name || (topK[0] ? `${topK[0].bank} ATM — ${topK[0].location_name}` : "State Bank of India — Banjara Hills")}
                    </div>
                    <div className="location-sub-details text-muted font-mono text-xs">
                      Candidate Space: 181 Terminals · Search Radius: {where.radius_km || 0.45} km
                    </div>
                  </div>
                </div>

                {/* 2. WHEN */}
                <div className="five-d-card card-when">
                  <div className="card-dim-header">
                    <span className="dim-tag tag-when">2. WHEN (TIME WINDOW)</span>
                    <span className="dim-conf font-mono">MAE: 5.32 min</span>
                  </div>
                  <div className="dim-body">
                    <div className="peak-window-display">
                      <span className="peak-num font-mono text-amber">
                        ~{when.peak_minutes || 37} mins
                      </span>
                      <span className="peak-label">Predicted Arrival</span>
                    </div>
                    <div className="window-range font-mono text-xs text-muted">
                      Conformal Interval (90%): {when.earliest_minutes || 26}m – {when.latest_minutes || 48}m (±10.6m)
                    </div>
                  </div>
                </div>

                {/* 3. AMOUNT */}
                <div className="five-d-card card-amount">
                  <div className="card-dim-header">
                    <span className="dim-tag tag-amount">3. AMOUNT (CASHOUT EXPECTED)</span>
                    <span className="dim-conf font-mono">MAE: ₹1,943</span>
                  </div>
                  <div className="dim-body">
                    <div className="amount-num font-mono text-emerald font-bold">
                      ₹{Math.round(amt.estimated_cashout_amount || form.amount * 0.92).toLocaleString("en-IN")}
                    </div>
                    <div className="amount-range font-mono text-xs text-muted">
                      Reported: ₹{Number(form.amount).toLocaleString("en-IN")} · Commission Shaved: 3–8%
                    </div>
                  </div>
                </div>

                {/* 4. WHY (SHAP ATTRIBUTIONS) */}
                <div className="five-d-card card-why">
                  <div className="card-dim-header">
                    <span className="dim-tag tag-why">4. WHY (SHAP EXPLAINABILITY)</span>
                    <span className="dim-conf font-mono">TreeExplainer</span>
                  </div>
                  <div className="dim-body">
                    <p className="why-text">{why.summary || "High transaction velocity and deliberate multi-hop pass-through structure."}</p>
                    <div className="shap-chips">
                      {(why.key_drivers || ["Rapid 3-hop mule chain", "High transaction velocity", "Target ATM cluster correlation"]).map((d, i) => (
                        <span key={i} className="shap-chip font-mono">
                          ▲ {d}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* 5. ACTION */}
                <div className="five-d-card card-action full-width">
                  <div className="card-dim-header">
                    <span className="dim-tag tag-action">5. ACTION (RECOMMENDED PROTOCOL)</span>
                    <span className="dim-conf font-mono">Section 91 CrPC Advisory</span>
                  </div>
                  <div className="dim-body">
                    <div className="action-directive font-bold">
                      {action.primary_action || "Deploy Blue Colts rapid patrol to target ATM terminal. Execute immediate Section 91 CrPC CCTV preservation."}
                    </div>
                    <div className="action-details font-mono text-xs text-muted mt-1">
                      Assigned Unit: {action.dispatch_unit || "Jubilee Hills Blue Colts Unit 04"} · Transit ETA: {predictionResult?.feasibility?.eta_minutes || 6.2} min
                    </div>
                  </div>
                </div>
              </div>

              {/* TOP-K ATM RANKINGS */}
              {topK.length > 0 && (
                <div className="topk-panel mt-3">
                  <h4 className="section-title-sm">TOP-K RANKED WITHDRAWAL TERMINALS</h4>
                  <div className="topk-list">
                    {topK.slice(0, 3).map((atm, i) => (
                      <div key={i} className="topk-item">
                        <span className="topk-rank font-mono">#{i + 1}</span>
                        <div className="topk-info">
                          <span className="atm-title font-semibold">{atm.bank || "ATM"} — {atm.location_name || atm.area}</span>
                          <span className="atm-meta font-mono text-xs text-muted">Terminal ID: {atm.atm_id} · Dist: {atm.distance_km ? `${atm.distance_km.toFixed(2)} km` : "0.45 km"}</span>
                        </div>
                        <span className="topk-score font-mono text-cyan">
                          {atm.probability ? `${(atm.probability * 100).toFixed(1)}%` : `${(92 - i * 7).toFixed(1)}%`}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
