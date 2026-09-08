/**
 * src/components/ComplaintForm.jsx — Project DRISHTI
 * Complaint submission form with preset demo scenarios.
 *
 * Props:
 *   onSubmit  {Function}  — called with the form payload object
 *   loading   {boolean}   — disables form while API call is in progress
 *   error     {string|null}
 */

import { useState } from "react";

// ── Demo presets for quick judge demo ─────────────────────────
const PRESETS = [
  {
    label: "UPI (Mumbai)",
    data: {
      complaint_text: "Mujhe Google Pay pe ek link aaya aur uspe click karne ke baad 35000 rupay nikal gaye. Bahut bura hua.",
      victim_lat: "19.076",
      victim_lon: "72.877",
      fraud_type: "upi_fraud",
      amount: "35000",
    },
  },
  {
    label: "KYC (Delhi)",
    data: {
      complaint_text: "Sir, koi mujhe WhatsApp pe message kiya aur bola ki KYC update nahi hua to account band ho jayega. Maine link pe Aadhaar dala aur 150000 rupay gaye.",
      victim_lat: "28.613",
      victim_lon: "77.209",
      fraud_type: "kyc_fraud",
      amount: "150000",
    },
  },
  {
    label: "Phishing (Bangalore)",
    data: {
      complaint_text: "IRCTC ticket cancel ka link aaya email pe, uspe details dali. Baad mein pata chala fraud tha. Rs 75000 ka nuksan hua.",
      victim_lat: "12.972",
      victim_lon: "77.594",
      fraud_type: "phishing",
      amount: "75000",
    },
  },
  {
    label: "UPI (Hyderabad)",
    data: {
      complaint_text: "Ek fraud number ne mujhe call karke bola SBI ka fraud department se bol raha hun. Transfer karwa liye 29000 rupay.",
      victim_lat: "17.385",
      victim_lon: "78.487",
      fraud_type: "upi_fraud",
      amount: "29000",
    },
  },
];

const FRAUD_TYPES = [
  { value: "", label: "Auto-detect (NLP)" },
  { value: "upi_fraud", label: "UPI Fraud" },
  { value: "kyc_fraud", label: "KYC Fraud" },
  { value: "phishing",  label: "Phishing" },
];

export default function ComplaintForm({ onSubmit, loading, error }) {
  const [form, setForm] = useState({
    complaint_text: "",
    victim_lat:     "",
    victim_lon:     "",
    fraud_type:     "",
    amount:         "",
    bank_account:   "",
    transaction_id: "",
  });

  function setField(key, value) {
    setForm(f => ({ ...f, [key]: value }));
  }

  function applyPreset(preset) {
    setForm(f => ({ ...f, ...preset.data }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (!form.complaint_text.trim()) return;

    // Build payload — only include non-empty fields
    const payload = { complaint_text: form.complaint_text.trim() };
    if (form.victim_lat)     payload.victim_lat     = parseFloat(form.victim_lat);
    if (form.victim_lon)     payload.victim_lon     = parseFloat(form.victim_lon);
    if (form.fraud_type)     payload.fraud_type     = form.fraud_type;
    if (form.amount)         payload.amount         = parseFloat(form.amount);
    if (form.bank_account)   payload.bank_account   = form.bank_account;
    if (form.transaction_id) payload.transaction_id = form.transaction_id;

    onSubmit(payload);
  }

  return (
    <form onSubmit={handleSubmit} className="left-panel" id="complaint-form">

      {/* Panel title */}
      <div className="panel-title">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
        </svg>
        Submit Complaint
      </div>

      {/* Quick-load presets */}
      <div>
        <div className="form-label" style={{ marginBottom: 6 }}>Quick Load Demo</div>
        <div className="presets-row">
          {PRESETS.map(p => (
            <button
              key={p.label}
              type="button"
              className="btn-preset"
              onClick={() => applyPreset(p)}
              id={`preset-${p.label.replace(/\s+/g,"-").toLowerCase()}`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Complaint text */}
      <div className="form-group">
        <label className="form-label" htmlFor="complaint-text">Complaint Text *</label>
        <textarea
          id="complaint-text"
          className="form-textarea"
          placeholder="Enter complaint in Hindi / English / Hinglish..."
          value={form.complaint_text}
          onChange={e => setField("complaint_text", e.target.value)}
          required
          rows={5}
        />
      </div>

      {/* Victim coordinates */}
      <div className="form-group">
        <label className="form-label">Victim Location (optional)</label>
        <div className="coord-row">
          <input
            id="victim-lat"
            type="number"
            className="form-input"
            placeholder="Latitude"
            step="any"
            value={form.victim_lat}
            onChange={e => setField("victim_lat", e.target.value)}
          />
          <input
            id="victim-lon"
            type="number"
            className="form-input"
            placeholder="Longitude"
            step="any"
            value={form.victim_lon}
            onChange={e => setField("victim_lon", e.target.value)}
          />
        </div>
      </div>

      {/* Fraud type */}
      <div className="form-group">
        <label className="form-label" htmlFor="fraud-type">Fraud Type</label>
        <select
          id="fraud-type"
          className="form-select"
          value={form.fraud_type}
          onChange={e => setField("fraud_type", e.target.value)}
        >
          {FRAUD_TYPES.map(ft => (
            <option key={ft.value} value={ft.value}>{ft.label}</option>
          ))}
        </select>
      </div>

      {/* Amount */}
      <div className="form-group">
        <label className="form-label" htmlFor="fraud-amount">Amount (INR)</label>
        <input
          id="fraud-amount"
          type="number"
          className="form-input"
          placeholder="e.g. 25000"
          min="0"
          value={form.amount}
          onChange={e => setField("amount", e.target.value)}
        />
      </div>

      {/* Optional structured fields */}
      <div className="form-group">
        <label className="form-label" htmlFor="bank-account">Bank Account (optional)</label>
        <input
          id="bank-account"
          type="text"
          className="form-input"
          placeholder="XXXX12345678"
          value={form.bank_account}
          onChange={e => setField("bank_account", e.target.value)}
        />
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="txn-id">Transaction ID (optional)</label>
        <input
          id="txn-id"
          type="text"
          className="form-input"
          placeholder="UPI1234567890"
          value={form.transaction_id}
          onChange={e => setField("transaction_id", e.target.value)}
        />
      </div>

      {/* Error message */}
      {error && (
        <div className="form-error" id="form-error">
          Error: {error}
        </div>
      )}

      {/* Submit */}
      <button
        type="submit"
        className="btn-predict"
        disabled={loading || !form.complaint_text.trim()}
        id="btn-analyze"
      >
        {loading ? (
          <>
            <div className="spinner" />
            Analyzing...
          </>
        ) : (
          <>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            Analyze &amp; Predict
          </>
        )}
      </button>
    </form>
  );
}
