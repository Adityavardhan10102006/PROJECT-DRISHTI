/**
 * src/components/IntelligenceSearchView.jsx — Project DRISHTI
 * ==========================================================
 * Universal Cybercrime Intelligence Search Interface.
 *
 * Capabilities:
 *   - Universal multi-entity query (Case, Complaint, Account, Transaction, ATM, Unit)
 *   - Transparent multi-factor relevance ranking
 *   - "Why this result?" investigative attribution
 *   - Multi-dimensional filters (Risk, Fraud Type, City, Bank, Amount Range)
 *   - Seamless navigation to Case Dossiers, Money Trail, Cash-Out Prospects, and Map
 */

import React, { useState, useEffect, useCallback } from "react";
import { searchIntelligence } from "../api.js";

export default function IntelligenceSearchView({
  onSelectCase,
  onNavigateTab,
  initialQuery = "",
  initialEntity = "all",
}) {
  const [query, setQuery] = useState(initialQuery);
  const [entityType, setEntityType] = useState(initialEntity);
  const [riskFilter, setRiskFilter] = useState("all");
  const [fraudTypeFilter, setFraudTypeFilter] = useState("all");
  const [cityFilter, setCityFilter] = useState("all");
  const [bankFilter, setBankFilter] = useState("all");
  const [minAmount, setMinAmount] = useState("");
  const [maxAmount, setMaxAmount] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  const [results, setResults] = useState([]);
  const [totalMatches, setTotalMatches] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchedOnce, setSearchedOnce] = useState(false);

  const executeSearch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await searchIntelligence({
        q: query,
        entity_type: entityType,
        risk: riskFilter !== "all" ? riskFilter : undefined,
        fraud_type: fraudTypeFilter !== "all" ? fraudTypeFilter : undefined,
        city: cityFilter !== "all" ? cityFilter : undefined,
        bank: bankFilter !== "all" ? bankFilter : undefined,
        min_amount: minAmount ? parseFloat(minAmount) : undefined,
        max_amount: maxAmount ? parseFloat(maxAmount) : undefined,
        limit: 60,
      });
      setResults(data.results || []);
      setTotalMatches(data.total_matches || 0);
      setSearchedOnce(true);
    } catch (err) {
      setError(err.message || "Failed to execute intelligence search");
    } finally {
      setLoading(false);
    }
  }, [query, entityType, riskFilter, fraudTypeFilter, cityFilter, bankFilter, minAmount, maxAmount]);

  // Initial search on mount
  useEffect(() => {
    executeSearch();
  }, [entityType, riskFilter, fraudTypeFilter]);

  const handleSubmit = (e) => {
    e.preventDefault();
    executeSearch();
  };

  const handleQuickChip = (term, type = "all") => {
    setQuery(term);
    setEntityType(type);
  };

  const getEntityIcon = (type) => {
    switch (type) {
      case "case": return "📁";
      case "complaint": return "📄";
      case "account": return "👤";
      case "transaction": return "💸";
      case "atm": return "🏧";
      case "unit": return "🚓";
      default: return "🔍";
    }
  };

  const getRiskClass = (risk) => {
    switch (risk?.toUpperCase()) {
      case "CRITICAL": return "badge-critical";
      case "HIGH": return "badge-high";
      case "MEDIUM": return "badge-medium";
      default: return "badge-low";
    }
  };

  return (
    <div className="search-view-container" style={{ padding: "20px 24px", color: "var(--text-primary)" }}>
      {/* Header Banner */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h1 style={{ margin: "0 0 6px 0", fontSize: 24, fontWeight: 800, letterSpacing: "-0.5px" }}>
              # INTELLIGENCE SEARCH
            </h1>
            <p style={{ margin: 0, fontSize: 13, color: "var(--text-muted)" }}>
              Universal Multi-Entity Cross-Correlation & Relevance Ranking Engine
            </p>
          </div>
          <div style={{
            fontSize: 11,
            padding: "4px 10px",
            borderRadius: 4,
            background: "rgba(59, 130, 246, 0.12)",
            border: "1px solid rgba(59, 130, 246, 0.3)",
            color: "#60a5fa",
            fontWeight: 700,
          }}>
            DATA SOURCE: Synthetic Demonstration Dataset
          </div>
        </div>
      </div>

      {/* Main Search Input Form */}
      <form onSubmit={handleSubmit} style={{ marginBottom: 16 }}>
        <div style={{
          display: "flex",
          gap: 10,
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: "6px 12px",
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.25)",
        }}>
          <span style={{ fontSize: 18, alignSelf: "center", color: "var(--text-muted)" }}>🔍</span>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search Case ID, Complaint, Account, ATM, ₹ Amount, UPI ID, or Police Unit..."
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              color: "var(--text-primary)",
              fontSize: 15,
              fontWeight: 500,
            }}
          />
          {query && (
            <button
              type="button"
              onClick={() => { setQuery(""); }}
              style={{
                background: "transparent",
                border: "none",
                color: "var(--text-muted)",
                cursor: "pointer",
                padding: "0 6px",
                fontSize: 16,
              }}
            >
              ✕
            </button>
          )}
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            style={{
              background: showFilters ? "rgba(59, 130, 246, 0.2)" : "rgba(255, 255, 255, 0.05)",
              border: `1px solid ${showFilters ? "#3b82f6" : "var(--border)"}`,
              borderRadius: 6,
              padding: "6px 12px",
              color: showFilters ? "#60a5fa" : "var(--text-secondary)",
              cursor: "pointer",
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            Filters {showFilters ? "▲" : "▼"}
          </button>
          <button
            type="submit"
            disabled={loading}
            style={{
              background: "var(--accent, #3b82f6)",
              border: "none",
              borderRadius: 6,
              padding: "6px 20px",
              color: "#fff",
              fontWeight: 700,
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </div>
      </form>

      {/* Entity Type Selector Tabs */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap", alignItems: "center" }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: "var(--text-muted)", marginRight: 4 }}>
          ENTITY TYPE:
        </span>
        {[
          { id: "all", label: "All Entities" },
          { id: "cases", label: "Cases" },
          { id: "complaints", label: "Complaints" },
          { id: "accounts", label: "Accounts" },
          { id: "transactions", label: "Transactions" },
          { id: "atms", label: "ATMs & Terminals" },
          { id: "units", label: "Response Units" },
        ].map((e) => (
          <button
            key={e.id}
            type="button"
            onClick={() => setEntityType(e.id)}
            style={{
              background: entityType === e.id ? "rgba(59, 130, 246, 0.25)" : "var(--surface)",
              border: `1px solid ${entityType === e.id ? "#3b82f6" : "var(--border)"}`,
              borderRadius: 20,
              padding: "4px 14px",
              fontSize: 12,
              fontWeight: entityType === e.id ? 700 : 500,
              color: entityType === e.id ? "#93c5fd" : "var(--text-secondary)",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            {e.label}
          </button>
        ))}
      </div>

      {/* Quick Filter Bar (Collapsible) */}
      {showFilters && (
        <div style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: "14px 16px",
          marginBottom: 16,
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 12,
        }}>
          <div>
            <label style={{ display: "block", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", marginBottom: 4 }}>
              RISK LEVEL
            </label>
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              style={{
                width: "100%",
                background: "var(--bg-primary)",
                border: "1px solid var(--border)",
                color: "var(--text-primary)",
                borderRadius: 4,
                padding: "6px 8px",
                fontSize: 12,
              }}
            >
              <option value="all">All Risk Levels</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", marginBottom: 4 }}>
              FRAUD TYPE
            </label>
            <select
              value={fraudTypeFilter}
              onChange={(e) => setFraudTypeFilter(e.target.value)}
              style={{
                width: "100%",
                background: "var(--bg-primary)",
                border: "1px solid var(--border)",
                color: "var(--text-primary)",
                borderRadius: 4,
                padding: "6px 8px",
                fontSize: 12,
              }}
            >
              <option value="all">All Fraud Types</option>
              <option value="upi">UPI Layering Fraud</option>
              <option value="phishing">Phishing Scam</option>
              <option value="kyc">KYC / Impersonation</option>
              <option value="investment">Investment Scam</option>
              <option value="card">Card / NetBanking</option>
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", marginBottom: 4 }}>
              BANK
            </label>
            <select
              value={bankFilter}
              onChange={(e) => setBankFilter(e.target.value)}
              style={{
                width: "100%",
                background: "var(--bg-primary)",
                border: "1px solid var(--border)",
                color: "var(--text-primary)",
                borderRadius: 4,
                padding: "6px 8px",
                fontSize: 12,
              }}
            >
              <option value="all">All Banks</option>
              <option value="SBI">State Bank of India (SBI)</option>
              <option value="HDFC">HDFC Bank</option>
              <option value="ICICI">ICICI Bank</option>
              <option value="AXIS">Axis Bank</option>
              <option value="KOTAK">Kotak Mahindra</option>
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", marginBottom: 4 }}>
              MIN AMOUNT (₹)
            </label>
            <input
              type="number"
              placeholder="e.g. 10000"
              value={minAmount}
              onChange={(e) => setMinAmount(e.target.value)}
              style={{
                width: "100%",
                background: "var(--bg-primary)",
                border: "1px solid var(--border)",
                color: "var(--text-primary)",
                borderRadius: 4,
                padding: "6px 8px",
                fontSize: 12,
              }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", marginBottom: 4 }}>
              MAX AMOUNT (₹)
            </label>
            <input
              type="number"
              placeholder="e.g. 200000"
              value={maxAmount}
              onChange={(e) => setMaxAmount(e.target.value)}
              style={{
                width: "100%",
                background: "var(--bg-primary)",
                border: "1px solid var(--border)",
                color: "var(--text-primary)",
                borderRadius: 4,
                padding: "6px 8px",
                fontSize: 12,
              }}
            />
          </div>

          <div style={{ display: "flex", alignItems: "flex-end" }}>
            <button
              type="button"
              onClick={() => {
                setRiskFilter("all");
                setFraudTypeFilter("all");
                setBankFilter("all");
                setCityFilter("all");
                setMinAmount("");
                setMaxAmount("");
              }}
              style={{
                width: "100%",
                background: "rgba(239, 68, 68, 0.15)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                color: "#f87171",
                borderRadius: 4,
                padding: "7px 12px",
                fontSize: 12,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Reset Filters
            </button>
          </div>
        </div>
      )}

      {/* Suggested Search Chips */}
      <div style={{ display: "flex", gap: 6, marginBottom: 20, alignItems: "center", flexWrap: "wrap" }}>
        <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600 }}>Suggested:</span>
        {[
          { label: "CASE-001 (UPI)", q: "CASE-001", type: "cases" },
          { label: "DR-2026-1001", q: "DR-2026-1001", type: "cases" },
          { label: "High Value ₹85,000", q: "85000", type: "all" },
          { label: "Hitec City ATMs", q: "Hitec City", type: "atms" },
          { label: "Mule Accounts", q: "mule", type: "accounts" },
          { label: "Cyberabad Units", q: "Cyberabad", type: "units" },
        ].map((chip, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleQuickChip(chip.q, chip.type)}
            style={{
              background: "rgba(255, 255, 255, 0.04)",
              border: "1px solid var(--border)",
              borderRadius: 4,
              padding: "3px 8px",
              fontSize: 11,
              color: "var(--text-secondary)",
              cursor: "pointer",
            }}
          >
            {chip.label}
          </button>
        ))}
      </div>

      {/* Results Section */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text-secondary)" }}>
          {loading ? "Searching..." : `${totalMatches} INTELLIGENCE ENTITIES IDENTIFIED`}
        </div>
        <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
          Ranked by Multi-Factor Composite Relevance
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div style={{
          background: "rgba(239, 68, 68, 0.12)",
          border: "1px solid #ef4444",
          color: "#f87171",
          borderRadius: 8,
          padding: "12px 16px",
          marginBottom: 16,
          fontSize: 13,
        }}>
          {error}
        </div>
      )}

      {/* Empty State */}
      {!loading && searchedOnce && results.length === 0 && (
        <div style={{
          textAlign: "center",
          padding: "48px 20px",
          background: "var(--surface)",
          border: "1px dashed var(--border)",
          borderRadius: 8,
          color: "var(--text-muted)",
        }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>🔍</div>
          <div style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>
            No intelligence entities match your search criteria.
          </div>
          <div style={{ fontSize: 13 }}>
            Try broadening your search term or clearing active filters.
          </div>
        </div>
      )}

      {/* Results Grid / List */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {results.map((r, idx) => {
          const relPct = Math.round((r.relevance_score || 0.5) * 100);
          return (
            <div
              key={`${r.entity_type}-${r.entity_id}-${idx}`}
              style={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                padding: "16px 18px",
                transition: "all 0.15s ease",
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.15)",
              }}
            >
              {/* Top Row: Entity Type, ID, Risk, Relevance */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                  <span style={{
                    fontSize: 10,
                    fontWeight: 800,
                    letterSpacing: "0.5px",
                    background: "rgba(59, 130, 246, 0.15)",
                    border: "1px solid rgba(59, 130, 246, 0.3)",
                    color: "#93c5fd",
                    padding: "2px 8px",
                    borderRadius: 4,
                  }}>
                    {getEntityIcon(r.entity_type)} {r.entity_type.toUpperCase()}
                  </span>
                  <span style={{ fontSize: 14, fontWeight: 800, color: "var(--text-primary)" }}>
                    {r.entity_id}
                  </span>
                  <span className={`badge ${getRiskClass(r.risk)}`} style={{ fontSize: 10, padding: "2px 8px" }}>
                    {r.risk} RISK
                  </span>
                  {r.location && (
                    <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                      📍 {r.location}
                    </span>
                  )}
                </div>

                {/* Relevance Score Pill */}
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{
                    width: 70,
                    height: 6,
                    background: "rgba(255, 255, 255, 0.08)",
                    borderRadius: 3,
                    overflow: "hidden",
                  }}>
                    <div style={{
                      width: `${relPct}%`,
                      height: "100%",
                      background: relPct > 80 ? "var(--accent, #3b82f6)" : (relPct > 60 ? "#10b981" : "#f59e0b"),
                    }} />
                  </div>
                  <span style={{ fontSize: 11, fontWeight: 700, color: "#93c5fd" }}>
                    {relPct}% Relevance
                  </span>
                </div>
              </div>

              {/* Title & Subtitle */}
              <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>
                {r.title}
              </div>
              <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 10 }}>
                {r.subtitle}
              </div>

              {/* "Why this result?" Explainability Attribution */}
              <div style={{
                background: "rgba(30, 41, 59, 0.6)",
                borderLeft: "3px solid var(--accent, #3b82f6)",
                padding: "8px 12px",
                borderRadius: "0 4px 4px 0",
                marginBottom: 12,
                fontSize: 12,
              }}>
                <span style={{ fontWeight: 700, color: "#93c5fd", marginRight: 6 }}>
                  Why this result?
                </span>
                <span style={{ color: "var(--text-secondary)" }}>
                  {r.relationship_summary}
                </span>
              </div>

              {/* Footer: Matched fields & Action buttons */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
                <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <span style={{ fontSize: 10, color: "var(--text-muted)" }}>Matched:</span>
                  {(r.matched_fields || []).map((f, i) => (
                    <span
                      key={i}
                      style={{
                        fontSize: 10,
                        background: "rgba(255, 255, 255, 0.05)",
                        padding: "1px 6px",
                        borderRadius: 3,
                        color: "var(--text-muted)",
                      }}
                    >
                      {f}
                    </span>
                  ))}
                </div>

                <div style={{ display: "flex", gap: 8 }}>
                  {r.entity_type === "case" && (
                    <button
                      type="button"
                      onClick={() => onSelectCase && onSelectCase(r.entity_id)}
                      style={{
                        background: "var(--accent, #3b82f6)",
                        border: "none",
                        borderRadius: 4,
                        padding: "5px 12px",
                        color: "#fff",
                        fontSize: 11,
                        fontWeight: 700,
                        cursor: "pointer",
                      }}
                    >
                      Open Case Dossier ➔
                    </button>
                  )}

                  {(r.entity_type === "account" || r.entity_type === "case") && (
                    <button
                      type="button"
                      onClick={() => onNavigateTab && onNavigateTab("money-trail")}
                      style={{
                        background: "rgba(255, 255, 255, 0.06)",
                        border: "1px solid var(--border)",
                        borderRadius: 4,
                        padding: "5px 12px",
                        color: "var(--text-primary)",
                        fontSize: 11,
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                    >
                      Trace Money Trail
                    </button>
                  )}

                  {r.entity_type === "atm" && (
                    <>
                      <button
                        type="button"
                        onClick={() => onNavigateTab && onNavigateTab("prospects")}
                        style={{
                          background: "var(--accent, #3b82f6)",
                          border: "none",
                          borderRadius: 4,
                          padding: "5px 12px",
                          color: "#fff",
                          fontSize: 11,
                          fontWeight: 700,
                          cursor: "pointer",
                        }}
                      >
                        Cash-Out Prospects ➔
                      </button>
                      <button
                        type="button"
                        onClick={() => onNavigateTab && onNavigateTab("command-center")}
                        style={{
                          background: "rgba(255, 255, 255, 0.06)",
                          border: "1px solid var(--border)",
                          borderRadius: 4,
                          padding: "5px 12px",
                          color: "var(--text-primary)",
                          fontSize: 11,
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                      >
                        View on Map
                      </button>
                    </>
                  )}

                  {r.entity_type === "transaction" && (
                    <button
                      type="button"
                      onClick={() => onNavigateTab && onNavigateTab("transactions")}
                      style={{
                        background: "rgba(255, 255, 255, 0.06)",
                        border: "1px solid var(--border)",
                        borderRadius: 4,
                        padding: "5px 12px",
                        color: "var(--text-primary)",
                        fontSize: 11,
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                    >
                      Inspect Ledger ➔
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
