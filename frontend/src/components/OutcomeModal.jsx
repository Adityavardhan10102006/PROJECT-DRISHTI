/**
 * src/components/OutcomeModal.jsx — Project DRISHTI
 * Field Outcome Validation & Continuous Improvement Modal.
 *
 * Allows police officers / SIH evaluators to record ground-truth outcomes:
 *   - Physical interception success
 *   - ATM location accuracy
 *   - Time window accuracy
 *   - Recovered INR amount
 *   - Continuous model retraining trigger
 */

import { useState } from "react";
import { submitOutcomeFeedback, triggerRetraining } from "../api";

export default function OutcomeModal({ prediction, onClose, onFeedbackSubmitted }) {
  const [wasIntercepted, setWasIntercepted] = useState(true);
  const [locationAccurate, setLocationAccurate] = useState(true);
  const [timeAccurate, setTimeAccurate] = useState(true);
  const [muleConfirmed, setMuleConfirmed] = useState(true);
  const [actualMinutes, setActualMinutes] = useState(prediction?.time_window?.peak_minutes || 35);
  const [recoveredAmount, setRecoveredAmount] = useState(prediction?.amount || 50000);
  const [officerBadge, setOfficerBadge] = useState("MH-CYBER-884");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [retraining, setRetraining] = useState(false);
  const [message, setMessage] = useState(null);

  if (!prediction) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      const payload = {
        complaint_id: prediction.complaint_id,
        was_intercepted: wasIntercepted,
        location_accurate: locationAccurate,
        time_window_accurate: timeAccurate,
        mule_confirmed: muleConfirmed,
        actual_withdrawal_minutes: Number(actualMinutes),
        recovered_amount: Number(recoveredAmount),
        officer_badge: officerBadge,
        notes: notes || undefined,
      };
      const targetAlertId = prediction.alert_id ?? prediction.complaint_id;
      await submitOutcomeFeedback(targetAlertId, payload);
      setMessage({ type: "success", text: "Outcome logged successfully in NCRP audit database!" });
      onFeedbackSubmitted?.();
      setTimeout(() => {
        onClose();
      }, 1200);
    } catch (err) {
      setMessage({ type: "error", text: err.message || "Failed to log outcome" });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRetrain() {
    setRetraining(true);
    setMessage(null);
    try {
      const res = await triggerRetraining();
      setMessage({
        type: "success",
        text: `Continuous Retraining Complete! Model Version: ${res.model_version} (Trained on ${res.samples_trained} samples)`
      });
    } catch (err) {
      setMessage({ type: "error", text: err.message || "Retraining failed" });
    } finally {
      setRetraining(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="modal-title">Field Outcome Validation</div>
            <div className="modal-subtitle">Case Ref: {prediction.complaint_id}</div>
          </div>
          <button className="modal-close-btn" onClick={onClose}>×</button>
        </div>

        {message && (
          <div className={`modal-alert ${message.type}`}>
            {message.text}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="modal-grid">
            <div className="toggle-group">
              <label>Physical Interception / Freeze Success?</label>
              <div className="toggle-buttons">
                <button
                  type="button"
                  className={`toggle-btn ${wasIntercepted ? "active-success" : ""}`}
                  onClick={() => setWasIntercepted(true)}
                >
                  YES (Intercepted)
                </button>
                <button
                  type="button"
                  className={`toggle-btn ${!wasIntercepted ? "active-danger" : ""}`}
                  onClick={() => setWasIntercepted(false)}
                >
                  NO (Missed)
                </button>
              </div>
            </div>

            <div className="toggle-group">
              <label>Location Prediction Accurate?</label>
              <div className="toggle-buttons">
                <button
                  type="button"
                  className={`toggle-btn ${locationAccurate ? "active-success" : ""}`}
                  onClick={() => setLocationAccurate(true)}
                >
                  Accurate (At Hotspot)
                </button>
                <button
                  type="button"
                  className={`toggle-btn ${!locationAccurate ? "active-danger" : ""}`}
                  onClick={() => setLocationAccurate(false)}
                >
                  Off Target
                </button>
              </div>
            </div>

            <div className="toggle-group">
              <label>Time Window Accurate?</label>
              <div className="toggle-buttons">
                <button
                  type="button"
                  className={`toggle-btn ${timeAccurate ? "active-success" : ""}`}
                  onClick={() => setTimeAccurate(true)}
                >
                  Within Window
                </button>
                <button
                  type="button"
                  className={`toggle-btn ${!timeAccurate ? "active-danger" : ""}`}
                  onClick={() => setTimeAccurate(false)}
                >
                  Outside Window
                </button>
              </div>
            </div>

            <div className="toggle-group">
              <label>Mule Account Syndicate Confirmed?</label>
              <div className="toggle-buttons">
                <button
                  type="button"
                  className={`toggle-btn ${muleConfirmed ? "active-success" : ""}`}
                  onClick={() => setMuleConfirmed(true)}
                >
                  Confirmed Mule Ring
                </button>
                <button
                  type="button"
                  className={`toggle-btn ${!muleConfirmed ? "active-danger" : ""}`}
                  onClick={() => setMuleConfirmed(false)}
                >
                  Innocent / False Flag
                </button>
              </div>
            </div>

            <div className="input-field">
              <label>Actual Time to Withdrawal (Minutes)</label>
              <input
                type="number"
                value={actualMinutes}
                onChange={e => setActualMinutes(e.target.value)}
                min={5}
                max={300}
                required
              />
            </div>

            <div className="input-field">
              <label>Recovered / Intercepted Amount (INR)</label>
              <input
                type="number"
                value={recoveredAmount}
                onChange={e => setRecoveredAmount(e.target.value)}
                min={0}
                required
              />
            </div>

            <div className="input-field">
              <label>Validating Officer ID / Badge</label>
              <input
                type="text"
                value={officerBadge}
                onChange={e => setOfficerBadge(e.target.value)}
                required
              />
            </div>

            <div className="input-field full-width">
              <label>Field Notes & Forensic Observations</label>
              <textarea
                value={notes}
                onChange={e => setNotes(e.target.value)}
                placeholder="e.g., Suspect apprehended at ATM vestibule; recovered 4 cloned debit cards and mobile handset."
                rows={2}
              />
            </div>
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="retrain-btn"
              onClick={handleRetrain}
              disabled={retraining}
            >
              {retraining ? "Retraining AI Models..." : "Trigger Continuous Retraining"}
            </button>
            <div style={{ display: "flex", gap: 8 }}>
              <button type="button" className="cancel-btn" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="submit-feedback-btn" disabled={submitting}>
                {submitting ? "Saving..." : "Submit Ground-Truth"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
