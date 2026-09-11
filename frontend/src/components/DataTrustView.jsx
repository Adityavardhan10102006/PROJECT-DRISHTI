import React from "react";

function ShieldCheckIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <polyline points="9 12 11 14 15 10" />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  );
}

export default function DataTrustView({ onNavigate }) {
  const handleExportGovernance = () => {
    const payload = {
      platform: "PROJECT DRISHTI",
      framework: "Predictive Analytics Framework for Cybercrime Complaints",
      data_governance_version: "1.0.0-PROTOTYPE",
      date_issued: new Date().toISOString(),
      classification: "SYNTHETIC DEMONSTRATION DATA",
      data_modes: {
        prototype: {
          status: "ACTIVE",
          data_types: [
            "Synthetic transaction graphs (5-hop layering)",
            "Curated geospatial ATM coordinates (Hyderabad cluster)",
            "Simulated citizen complaints (NCRP format compliant)",
            "Synthetic mule accounts with masked identifiers",
          ],
          disclaimer: "No live banking feeds or real citizen PII are ingested in this prototype environment.",
        },
        potential_production_integration: {
          status: "FUTURE_AUTHORIZED_INTEGRATION",
          potential_sources: [
            "National Cybercrime Reporting Portal (NCRP / I4C)",
            "Citizen Financial Cyber Fraud Reporting and Management System (CFCFRMS)",
            "Participating Core Banking Systems via Secure API Gateway",
            "Authorized State Police Dispatch / GIS Patrol Systems",
            "Indian Cyber Crime Coordination Centre (I4C) Suspect Registry",
          ],
          statutory_safeguards: [
            "Section 91 CrPC (Summons to produce document)",
            "Information Technology Act, 2000 (Section 69 & 79A)",
            "Digital Personal Data Protection Act, 2023 (DPDPA)",
            "Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)",
          ],
        },
      },
      privacy_architecture: {
        tokenization: "SHA-256 account masking with pseudorandom salts",
        data_minimization: "Strict ingestion of only transaction amount, timestamp, IFSC, and routing hop",
        access_control: "Role-Based Access Control (RBAC) — Admin, Analyst, Investigator",
        human_in_the_loop: "Predictive decision support only; final operational mandate requires human authorization",
        audit_trail: "Cryptographically linked chronological action logs",
      },
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `DRISHTI_DATA_GOVERNANCE_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="overview-container" style={{ maxWidth: "1200px", margin: "0 auto" }}>
      {/* ── 1. HEADER & HERO ── */}
      <div className="view-header" style={{ flexWrap: "wrap", gap: "16px", marginBottom: "20px" }}>
        <div>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
            <span style={{ color: "var(--red-bright)" }}>
              <ShieldCheckIcon />
            </span>
            <span style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "1px", textTransform: "uppercase", color: "var(--red-bright)" }}>
              DATA GOVERNANCE &amp; ETHICS
            </span>
          </div>
          <h1 className="view-title" style={{ fontSize: "24px", letterSpacing: "0.5px" }}>
            DRISHTI DATA &amp; TRUST ARCHITECTURE
          </h1>
          <p className="view-subtitle" style={{ fontSize: "14px", color: "var(--text-secondary)", marginTop: "4px" }}>
            &ldquo;Authorized data in. Predictive intelligence out.&rdquo;
          </p>
        </div>

        <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
          {onNavigate && (
            <button
              type="button"
              className="btn-primary-action"
              onClick={() => onNavigate("pipeline", "CASE-001-UPI-CRITICAL")}
              title="Inspect 5D Prediction Pipeline"
            >
              <span>⚡ 5D PIPELINE</span>
              <span>→</span>
            </button>
          )}

          <button
            type="button"
            className="chip-btn"
            onClick={handleExportGovernance}
            title="Download full data governance specification as JSON"
          >
            📥 EXPORT SPECIFICATION
          </button>
        </div>
      </div>

      {/* ── 2. DATA HONESTY: DUAL MODES COMPARISON ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "16px", marginBottom: "24px" }}>
        {/* Box A: Current Prototype */}
        <div
          className="panel-card"
          style={{
            borderLeft: "4px solid var(--warning)",
            background: "linear-gradient(180deg, rgba(245, 165, 36, 0.04) 0%, var(--surface) 100%)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
            <div>
              <span className="badge-tag" style={{ background: "rgba(245, 165, 36, 0.15)", color: "var(--warning)", border: "1px solid rgba(245, 165, 36, 0.4)", fontSize: "10.5px" }}>
                CURRENT PROTOTYPE
              </span>
              <h3 style={{ fontSize: "16px", fontWeight: 700, color: "var(--text-primary)", marginTop: "8px" }}>
                Synthetic Demonstration Data
              </h3>
            </div>
            <span style={{ fontSize: "20px" }}>🧪</span>
          </div>

          <p style={{ fontSize: "12.5px", color: "var(--text-secondary)", lineHeight: "1.5", marginBottom: "14px" }}>
            The current evaluation sandbox operates entirely on high-fidelity synthetic benchmark datasets engineered to replicate Indian cyber fraud typologies without exposing citizen records.
          </p>

          <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "8px", fontSize: "12px" }}>
            <li style={{ display: "flex", alignItems: "flex-start", gap: "8px", color: "var(--text-primary)" }}>
              <span style={{ color: "var(--warning)" }}>✓</span>
              <span><strong>Synthetic Transaction Trails:</strong> 15,000 multi-hop synthetic ledger records modeling rapid UPI mule cascades.</span>
            </li>
            <li style={{ display: "flex", alignItems: "flex-start", gap: "8px", color: "var(--text-primary)" }}>
              <span style={{ color: "var(--warning)" }}>✓</span>
              <span><strong>Curated Geospatial ATMs:</strong> 520 real physical ATM coordinates in the Hyderabad cluster for spatial testing.</span>
            </li>
            <li style={{ display: "flex", alignItems: "flex-start", gap: "8px", color: "var(--text-primary)" }}>
              <span style={{ color: "var(--warning)" }}>✓</span>
              <span><strong>Compliant NCRP Schemas:</strong> Formatted to mirror National Cybercrime Reporting Portal complaint structures.</span>
            </li>
            <li style={{ display: "flex", alignItems: "flex-start", gap: "8px", color: "var(--text-primary)" }}>
              <span style={{ color: "var(--warning)" }}>✓</span>
              <span><strong>No Live Banking Feeds:</strong> Zero live bank accounts or citizen PII utilized in demonstration mode.</span>
            </li>
          </ul>
        </div>

        {/* Box B: Potential Production Integration */}
        <div
          className="panel-card"
          style={{
            borderLeft: "4px solid var(--red-bright)",
            background: "linear-gradient(180deg, rgba(229, 9, 20, 0.04) 0%, var(--surface) 100%)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
            <div>
              <span className="badge-tag" style={{ background: "rgba(229, 9, 20, 0.15)", color: "var(--red-bright)", border: "1px solid rgba(229, 9, 20, 0.4)", fontSize: "10.5px" }}>
                FUTURE / AUTHORIZED INTEGRATION
              </span>
              <h3 style={{ fontSize: "16px", fontWeight: 700, color: "var(--text-primary)", marginTop: "8px" }}>
                Potential Production Ecosystem
              </h3>
            </div>
            <span style={{ fontSize: "20px" }}>🏛️</span>
          </div>

          <p style={{ fontSize: "12.5px", color: "var(--text-secondary)", lineHeight: "1.5", marginBottom: "14px" }}>
            In production deployment, DRISHTI is architected to ingest data exclusively through secured, permissioned statutory gateways authorized by law enforcement authorities.
          </p>

          <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "8px", fontSize: "12px" }}>
            <li style={{ display: "flex", alignItems: "flex-start", gap: "8px", color: "var(--text-primary)" }}>
              <span style={{ color: "var(--red-bright)" }}>⬡</span>
              <span><strong>NCRP &amp; CFCFRMS:</strong> Ingestion of national cybercrime complaints and bank freeze notifications (1930 Helpline).</span>
            </li>
            <li style={{ display: "flex", alignItems: "flex-start", gap: "8px", color: "var(--text-primary)" }}>
              <span style={{ color: "var(--red-bright)" }}>⬡</span>
              <span><strong>Participating Financial Institutions:</strong> Bank API hooks under statutory notice protocols for real-time mule flags.</span>
            </li>
            <li style={{ display: "flex", alignItems: "flex-start", gap: "8px", color: "var(--text-primary)" }}>
              <span style={{ color: "var(--red-bright)" }}>⬡</span>
              <span><strong>I4C Suspect Registry:</strong> Suspect repository cross-matching (Samanvaya / Pratibimb data sharing).</span>
            </li>
            <li style={{ display: "flex", alignItems: "flex-start", gap: "8px", color: "var(--text-primary)" }}>
              <span style={{ color: "var(--red-bright)" }}>⬡</span>
              <span><strong>State Police Dispatch:</strong> Automated tactical alert routing to designated field response patrols.</span>
            </li>
          </ul>
        </div>
      </div>

      {/* ── 3. ARCHITECTURE FLOW: DATA IN TO INTELLIGENCE OUT ── */}
      <div className="panel-card" style={{ marginBottom: "24px" }}>
        <div className="panel-header" style={{ marginBottom: "16px" }}>
          <div>
            <h2 className="panel-title" style={{ fontSize: "15px" }}>
              INGESTION &amp; PREDICTION PIPELINE ARCHITECTURE
            </h2>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              Statutory verification gate between raw complaint inputs and operational investigator action
            </span>
          </div>
          <span className="badge-tag badge-risk-low">STATUTORY COMPLIANCE</span>
        </div>

        {/* Visual Architecture Diagram */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: "10px", alignItems: "center" }}>
          {/* Step 1 */}
          <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", padding: "14px 12px", textAlign: "center" }}>
            <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--red-bright)", letterSpacing: "0.5px" }}>STAGE 01</div>
            <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)", margin: "4px 0" }}>AUTHORIZED SOURCES</div>
            <div style={{ fontSize: "10.5px", color: "var(--text-muted)" }}>NCRP · 1930 Helpline · CFCFRMS · Banks</div>
          </div>

          <div style={{ textAlign: "center", color: "var(--red-bright)", fontSize: "18px", fontWeight: 700 }}>↓</div>

          {/* Step 2 */}
          <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", padding: "14px 12px", textAlign: "center" }}>
            <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--red-bright)", letterSpacing: "0.5px" }}>STAGE 02</div>
            <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)", margin: "4px 0" }}>SECURE INGESTION</div>
            <div style={{ fontSize: "10.5px", color: "var(--text-muted)" }}>Tokenized Identifiers · Mutual TLS · HMAC</div>
          </div>

          <div style={{ textAlign: "center", color: "var(--red-bright)", fontSize: "18px", fontWeight: 700 }}>↓</div>

          {/* Step 3 */}
          <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", padding: "14px 12px", textAlign: "center" }}>
            <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--red-bright)", letterSpacing: "0.5px" }}>STAGE 03</div>
            <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)", margin: "4px 0" }}>DATA VALIDATION</div>
            <div style={{ fontSize: "10.5px", color: "var(--text-muted)" }}>Schema Hygiene · Duplicate Cull · Ledger Check</div>
          </div>

          <div style={{ textAlign: "center", color: "var(--red-bright)", fontSize: "18px", fontWeight: 700 }}>↓</div>

          {/* Step 4 */}
          <div style={{ background: "rgba(229, 9, 20, 0.08)", border: "1px solid rgba(229, 9, 20, 0.35)", borderRadius: "var(--radius-sm)", padding: "14px 12px", textAlign: "center" }}>
            <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--red-bright)", letterSpacing: "0.5px" }}>STAGE 04 · CORE</div>
            <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)", margin: "4px 0" }}>DRISHTI ML ENGINES</div>
            <div style={{ fontSize: "10.5px", color: "var(--text-muted)" }}>NetworkX · XGBoost · RF · Regressor</div>
          </div>

          <div style={{ textAlign: "center", color: "var(--red-bright)", fontSize: "18px", fontWeight: 700 }}>↓</div>

          {/* Step 5 */}
          <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", padding: "14px 12px", textAlign: "center" }}>
            <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--red-bright)", letterSpacing: "0.5px" }}>STAGE 05</div>
            <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)", margin: "4px 0" }}>5D INTELLIGENCE</div>
            <div style={{ fontSize: "10.5px", color: "var(--text-muted)" }}>WHERE · WHEN · AMOUNT · WHY · ACTION</div>
          </div>

          <div style={{ textAlign: "center", color: "var(--red-bright)", fontSize: "18px", fontWeight: 700 }}>↓</div>

          {/* Step 6 */}
          <div style={{ background: "rgba(33, 199, 122, 0.08)", border: "1px solid rgba(33, 199, 122, 0.35)", borderRadius: "var(--radius-sm)", padding: "14px 12px", textAlign: "center" }}>
            <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--success)", letterSpacing: "0.5px" }}>STAGE 06 · HUMAN</div>
            <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--success)", margin: "4px 0" }}>AUTHORIZED OFFICER</div>
            <div style={{ fontSize: "10.5px", color: "var(--text-muted)" }}>Section 91 CrPC Notice · Field Dispatch</div>
          </div>
        </div>
      </div>

      {/* ── 4. PRIVACY-FIRST INTELLIGENCE PILLARS ── */}
      <div className="panel-card" style={{ marginBottom: "24px" }}>
        <div className="panel-header" style={{ marginBottom: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ color: "var(--red-bright)" }}><LockIcon /></span>
            <h2 className="panel-title" style={{ fontSize: "15px" }}>
              🔐 PRIVACY-FIRST INTELLIGENCE SAFEGUARDS
            </h2>
          </div>
          <span className="badge-tag" style={{ background: "rgba(229, 9, 20, 0.12)", color: "var(--red-bright)" }}>
            ZERO PII EXPOSURE
          </span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "14px" }}>
          <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", padding: "14px" }}>
            <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)", marginBottom: "4px" }}>
              ✓ Minimum Necessary Ingestion
            </div>
            <p style={{ fontSize: "11.5px", color: "var(--text-secondary)", lineHeight: "1.4", margin: 0 }}>
              The system strictly avoids collecting unnecessary personal identity documents, biometric data, PINs, OTPs, or passwords. Analytical pipelines only process routing hop mechanics, transaction timestamps, and amount differentials.
            </p>
          </div>

          <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", padding: "14px" }}>
            <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)", marginBottom: "4px" }}>
              ✓ Tokenized &amp; Masked Identifiers
            </div>
            <p style={{ fontSize: "11.5px", color: "var(--text-secondary)", lineHeight: "1.4", margin: 0 }}>
              Bank account numbers are tokenized to irreversible cryptographic hashes. Operational dashboards mask intermediate mule accounts as <code className="font-mono" style={{ color: "var(--amber)" }}>XXXXXX1012</code> and victim identities as <code className="font-mono" style={{ color: "var(--red-bright)" }}>SUBJ-00481</code>.
            </p>
          </div>

          <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", padding: "14px" }}>
            <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)", marginBottom: "4px" }}>
              ✓ Strict Role-Based Access Control (RBAC)
            </div>
            <p style={{ fontSize: "11.5px", color: "var(--text-secondary)", lineHeight: "1.4", margin: 0 }}>
              Authenticated sessions distinguish between Administrators, Intelligence Analysts, and Field Duty Officers. Data decryption keys and raw bank identifiers are strictly gated to authorized supervisory accounts.
            </p>
          </div>

          <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", padding: "14px" }}>
            <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)", marginBottom: "4px" }}>
              ✓ Immutable Cryptographic Audit Log
            </div>
            <p style={{ fontSize: "11.5px", color: "var(--text-secondary)", lineHeight: "1.4", margin: 0 }}>
              Every case inquiry, model inference, prediction export, and requisition draft generates an auditable tamper-evident record timestamped with user credentials and IP provenance in compliance with Section 65B of the Indian Evidence Act.
            </p>
          </div>

          <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", padding: "14px" }}>
            <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)", marginBottom: "4px" }}>
              ✓ Human-in-the-Loop Operational Mandate
            </div>
            <p style={{ fontSize: "11.5px", color: "var(--text-secondary)", lineHeight: "1.4", margin: 0 }}>
              DRISHTI explicitly does <strong>NOT</strong> perform autonomous account freezes or autonomous police arrests. All predictive outputs are packaged as evidentiary decision-support dossiers requiring human investigator sign-off.
            </p>
          </div>

          <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", padding: "14px" }}>
            <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)", marginBottom: "4px" }}>
              ✓ Statutory Compliance Framework
            </div>
            <p style={{ fontSize: "11.5px", color: "var(--text-secondary)", lineHeight: "1.4", margin: 0 }}>
              Designed to operate within the procedural bounds of Section 91 CrPC (Notice to Produce), Section 106 BNSS, Information Technology Act 2000, and the Digital Personal Data Protection Act (DPDPA), 2023.
            </p>
          </div>
        </div>
      </div>

      {/* ── 5. STATUTORY BANNER ── */}
      <div
        className="panel-card"
        style={{
          background: "rgba(18, 21, 27, 0.8)",
          borderColor: "rgba(229, 9, 20, 0.3)",
          padding: "16px 20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "14px",
        }}
      >
        <div style={{ maxWidth: "780px" }}>
          <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--red-bright)", letterSpacing: "0.5px", textTransform: "uppercase" }}>
            Operational Doctrine
          </div>
          <div style={{ fontSize: "13px", color: "var(--text-primary)", marginTop: "3px", lineHeight: "1.5" }}>
            <strong>Automated Predictive Analytics + Human Supervisory Authorization = Lawful Intervention.</strong>
            <span style={{ color: "var(--text-secondary)", display: "block", fontSize: "12px", marginTop: "2px" }}>
              Algorithms forecast high-probability withdrawal coordinates and time windows to position field patrol units proactively. Final investigative notices and operational actions remain under the direct authority of sworn law enforcement personnel.
            </span>
          </div>
        </div>

        <div style={{ display: "flex", gap: "8px" }}>
          {onNavigate && (
            <button
              type="button"
              className="chip-btn"
              onClick={() => onNavigate("cases")}
              style={{ fontSize: "12px" }}
            >
              📋 Cases Registry
            </button>
          )}
          {onNavigate && (
            <button
              type="button"
              className="btn-primary-action"
              onClick={() => onNavigate("pipeline", "CASE-001-UPI-CRITICAL")}
              style={{ fontSize: "12px", padding: "6px 12px" }}
            >
              <span>⚡ Live Pipeline</span>
              <span>→</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
