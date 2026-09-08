/**
 * src/components/AboutModal.jsx — Project DRISHTI
 * Law Enforcement Tactical Overview & SIH 2026 Context.
 *
 * SIH26184 — Ministry of Home Affairs | Blockchain & Cybersecurity
 */

export default function AboutModal({ onClose }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="about-modal-content" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="about-modal-header">
          <div className="about-title-group">
            <div className="about-sih-tag">SIH 2026 · PROBLEM STATEMENT SIH26184</div>
            <h2 className="about-main-title">PROJECT DRISHTI</h2>
            <div className="about-subtitle">
              Detection and Real-time Intelligence for Surveillance, Hotspot Tracking, and Interception
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} title="Close">×</button>
        </div>

        {/* Content Body */}
        <div className="about-body">
          {/* Section 1: Executive Summary */}
          <div className="about-section">
            <div className="about-section-title">
              <span className="about-icon">🏛️</span> Ministry of Home Affairs (MHA) Problem Statement
            </div>
            <p className="about-text">
              In financial cybercrimes (UPI fraud, KYC phishing, investment scams), criminals rapidly transfer stolen funds across multiple mule accounts before executing physical cash withdrawals at ATMs within a critical <strong>30–60 minute golden window</strong>.
            </p>
            <p className="about-text">
              <strong>Project DRISHTI</strong> provides law-enforcement agencies with a predictive analytics framework that transforms raw cybercrime complaint text into <strong>5D Actionable Intelligence</strong> in sub-second latency, enabling tactical patrol dispatch and account freezing before the money vanishes into cash.
            </p>
          </div>

          {/* Section 2: 5D Intelligence Dimensions */}
          <div className="about-section">
            <div className="about-section-title">
              <span className="about-icon">🎯</span> The 5D Predictive Intelligence Framework
            </div>
            <div className="five-d-grid">
              <div className="five-d-card">
                <div className="five-d-card-header">
                  <span className="five-d-dim dim-where">WHERE</span>
                  <span className="five-d-tech">DBSCAN Clustering</span>
                </div>
                <div className="five-d-card-body">
                  Forecasts Top-K candidate ATM withdrawal clusters and spatial perimeters from ATM density and victim origin coordinates.
                </div>
              </div>

              <div className="five-d-card">
                <div className="five-d-card-header">
                  <span className="five-d-dim dim-when">WHEN</span>
                  <span className="five-d-tech">XGBoost Regressor</span>
                </div>
                <div className="five-d-card-body">
                  Predicts the exact minutes-to-withdrawal window and peak interception deadline based on fraud type and diversion velocity.
                </div>
              </div>

              <div className="five-d-card">
                <div className="five-d-card-header">
                  <span className="five-d-dim dim-amount">AMOUNT</span>
                  <span className="five-d-tech">Syndicate Cut Model</span>
                </div>
                <div className="five-d-card-body">
                  Computes net cash-out volume arriving at the ATM after accounting for multi-tier mule network laundering fee cuts.
                </div>
              </div>

              <div className="five-d-card">
                <div className="five-d-card-header">
                  <span className="five-d-dim dim-why">WHY</span>
                  <span className="five-d-tech">GradientBoosting + SHAP</span>
                </div>
                <div className="five-d-card-body">
                  0–100 AI Case Risk score with explainability feature attributions detailing why a case is prioritized.
                </div>
              </div>

              <div className="five-d-card five-d-card-wide">
                <div className="five-d-card-header">
                  <span className="five-d-dim dim-action">ACTION</span>
                  <span className="five-d-tech">Haversine Police Feasibility</span>
                </div>
                <div className="five-d-card-body">
                  Automatically pairs the case with the nearest patrol station, calculates vehicle ETA, computes interception margin, and issues tactical police SOP directives.
                </div>
              </div>
            </div>
          </div>

          {/* Section 3: Architecture & Tech Stack */}
          <div className="about-section">
            <div className="about-section-title">
              <span className="about-icon">⚡</span> High-Performance Local Architecture
            </div>
            <div className="about-tech-badges">
              <span className="tech-badge"><strong>Backend:</strong> FastAPI (Python 3.10+)</span>
              <span className="tech-badge"><strong>Frontend:</strong> React 18 + Leaflet GIS</span>
              <span className="tech-badge"><strong>NLP:</strong> Multilingual Hindi/English Parser</span>
              <span className="tech-badge"><strong>Mule Graph:</strong> NetworkX Directed Graph</span>
              <span className="tech-badge"><strong>Time Model:</strong> XGBoost v2.0 (MAE ~6.2m)</span>
              <span className="tech-badge"><strong>Risk Model:</strong> Gradient Boosting Classifier (88.4% Acc)</span>
              <span className="tech-badge"><strong>Spatial:</strong> Scikit-Learn DBSCAN</span>
              <span className="tech-badge"><strong>Learning:</strong> Active Feedback Loop Retraining</span>
            </div>
          </div>

          {/* Section 4: Closed-Loop Continuous Improvement */}
          <div className="about-section">
            <div className="about-section-title">
              <span className="about-icon">🔄</span> Closed-Loop Operator Feedback
            </div>
            <p className="about-text">
              Every dispatched unit logs ground-truth interception results via the <strong>Validate Outcome</strong> interface. Once verified, the feedback engine ingests the audit records to incrementally retrain the predictive risk and time models without service disruption.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="about-modal-footer">
          <div className="about-compliance-note">
            <span>🔒 Law Enforcement Ops · Ministry of Home Affairs (SIH 2026)</span>
          </div>
          <button className="about-close-action-btn" onClick={onClose}>
            Close &amp; Return to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
