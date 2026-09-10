/**
 * frontend/src/components/TransactionsView.jsx
 * Enterprise Financial Transactions Ledger for Project DRISHTI.
 * Features:
 *   - Search and filtering across 22,000+ transactions
 *   - Financial aggregates (Volume, Velocity, Fraud Ratio, Bank Distribution)
 *   - Responsive table wrapper with sticky header and pagination
 *   - Direct navigation to Case Dossier
 */

import { useState, useEffect } from "react";
import { fetchTransactions, fetchTransactionStats } from "../api";

export default function TransactionsView({ onSelectCase }) {
  const [transactions, setTransactions] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const limit = 30;

  // Filter States
  const [search, setSearch] = useState("");
  const [accountFilter, setAccountFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [fraudFilter, setFraudFilter] = useState("");
  const [minAmount, setMinAmount] = useState("");
  const [maxAmount, setMaxAmount] = useState("");

  const loadData = async (offset = 0) => {
    try {
      setLoading(true);
      const [txRes, statsRes] = await Promise.all([
        fetchTransactions({
          search: search || undefined,
          account: accountFilter || undefined,
          transaction_type: typeFilter || undefined,
          is_fraud: fraudFilter !== "" ? parseInt(fraudFilter) : undefined,
          min_amount: minAmount ? parseFloat(minAmount) : undefined,
          max_amount: maxAmount ? parseFloat(maxAmount) : undefined,
          limit,
          offset,
        }),
        fetchTransactionStats(),
      ]);
      setTransactions(txRes.transactions || []);
      setTotalCount(txRes.total || 0);
      setStats(statsRes);
    } catch (err) {
      console.error("Failed to load transactions:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setPage(0);
    loadData(0);
  }, [typeFilter, fraudFilter]);

  const handleApplyFilters = (e) => {
    e.preventDefault();
    setPage(0);
    loadData(0);
  };

  const handleReset = () => {
    setSearch("");
    setAccountFilter("");
    setTypeFilter("");
    setFraudFilter("");
    setMinAmount("");
    setMaxAmount("");
    setPage(0);
    setTimeout(() => loadData(0), 10);
  };

  const handlePageChange = (newPage) => {
    setPage(newPage);
    loadData(newPage * limit);
  };

  return (
    <div className="transactions-view-container" style={{ padding: "20px 24px", display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Top Title & Stats Strip */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 14 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <h1 style={{ fontSize: 20, fontWeight: 800, margin: 0, color: "var(--text-primary)" }}>
              Financial Transactions Ledger
            </h1>
            <span style={{
              fontSize: 10,
              fontWeight: 800,
              padding: "3px 8px",
              borderRadius: 4,
              background: "rgba(56, 189, 248, 0.15)",
              color: "#38bdf8",
              border: "1px solid #0284c7",
            }}>
              22,000+ OBSERVATIONS
            </span>
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
            Inter-bank transaction flows, multi-hop money-mule transfers, and cash withdrawal attempts.
          </div>
        </div>

        {stats && (
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <div style={{ background: "#0c1322", border: "1px solid var(--border)", borderRadius: 6, padding: "8px 14px", textAlign: "right" }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>Fraud Siphoned</div>
              <div style={{ fontSize: 16, fontWeight: 800, color: "#f87171" }}>₹{(stats.fraud_volume_inr || 0).toLocaleString()}</div>
            </div>
            <div style={{ background: "#0c1322", border: "1px solid var(--border)", borderRadius: 6, padding: "8px 14px", textAlign: "right" }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>Fraud Ratio</div>
              <div style={{ fontSize: 16, fontWeight: 800, color: "#f59e0b" }}>{stats.fraud_ratio_pct || 0}%</div>
            </div>
          </div>
        )}
      </div>

      {/* Filter Toolbar */}
      <form
        onSubmit={handleApplyFilters}
        style={{
          background: "#0c1322",
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: "14px 18px",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 12,
          alignItems: "flex-end",
        }}
      >
        <div>
          <label style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", display: "block", marginBottom: 4 }}>
            Search Account / Device / Txn
          </label>
          <input
            type="text"
            placeholder="Search keyword..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: "100%",
              background: "#080d1a",
              border: "1px solid var(--border)",
              borderRadius: 4,
              padding: "7px 10px",
              color: "var(--text-primary)",
              fontSize: 12,
            }}
          />
        </div>

        <div>
          <label style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", display: "block", marginBottom: 4 }}>
            Transaction Type
          </label>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            style={{
              width: "100%",
              background: "#080d1a",
              border: "1px solid var(--border)",
              borderRadius: 4,
              padding: "7px 10px",
              color: "var(--text-primary)",
              fontSize: 12,
            }}
          >
            <option value="">All Types</option>
            <option value="UPI">UPI Transfer</option>
            <option value="IMPS">IMPS Mule Relay</option>
            <option value="ATM_WITHDRAWAL">ATM Cash Withdrawal</option>
            <option value="NEFT">NEFT Settlement</option>
            <option value="RTGS">RTGS Wire</option>
          </select>
        </div>

        <div>
          <label style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", display: "block", marginBottom: 4 }}>
            Fraud Flag
          </label>
          <select
            value={fraudFilter}
            onChange={(e) => setFraudFilter(e.target.value)}
            style={{
              width: "100%",
              background: "#080d1a",
              border: "1px solid var(--border)",
              borderRadius: 4,
              padding: "7px 10px",
              color: "var(--text-primary)",
              fontSize: 12,
            }}
          >
            <option value="">All Transactions</option>
            <option value="1">Fraud Only (Mule / Terminal)</option>
            <option value="0">Legitimate Retail Only</option>
          </select>
        </div>

        <div>
          <label style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", display: "block", marginBottom: 4 }}>
            Min Amount (₹)
          </label>
          <input
            type="number"
            placeholder="e.g. 20000"
            value={minAmount}
            onChange={(e) => setMinAmount(e.target.value)}
            style={{
              width: "100%",
              background: "#080d1a",
              border: "1px solid var(--border)",
              borderRadius: 4,
              padding: "7px 10px",
              color: "var(--text-primary)",
              fontSize: 12,
            }}
          />
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <button
            type="submit"
            style={{
              flex: 1,
              background: "#38bdf8",
              color: "#080c18",
              border: "none",
              borderRadius: 4,
              padding: "8px",
              fontSize: 12,
              fontWeight: 800,
              cursor: "pointer",
            }}
          >
            Filter
          </button>
          <button
            type="button"
            onClick={handleReset}
            style={{
              background: "#1e293b",
              color: "var(--text-secondary)",
              border: "1px solid var(--border)",
              borderRadius: 4,
              padding: "8px 12px",
              fontSize: 12,
              cursor: "pointer",
            }}
          >
            Reset
          </button>
        </div>
      </form>

      {/* Transaction Table with Horizontal Scroll Wrapper */}
      <div style={{ background: "#0c1322", border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
        <div style={{
          padding: "12px 18px",
          background: "#080d1a",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: 12,
        }}>
          <div style={{ color: "var(--text-muted)" }}>
            Showing <strong>{transactions.length}</strong> of <strong>{totalCount.toLocaleString()}</strong> matched records
          </div>
          <div style={{ color: "var(--text-secondary)" }}>
            Page {page + 1} of {Math.max(1, Math.ceil(totalCount / limit))}
          </div>
        </div>

        <div className="table-responsive-wrapper" style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, textAlign: "left" }}>
            <thead>
              <tr style={{ background: "#060a14", borderBottom: "1px solid var(--border)" }}>
                <th style={{ padding: "10px 14px", color: "#94a3b8", fontWeight: 700, whiteSpace: "nowrap" }}>TXN ID</th>
                <th style={{ padding: "10px 14px", color: "#94a3b8", fontWeight: 700, whiteSpace: "nowrap" }}>TIMESTAMP</th>
                <th style={{ padding: "10px 14px", color: "#94a3b8", fontWeight: 700, whiteSpace: "nowrap" }}>AMOUNT</th>
                <th style={{ padding: "10px 14px", color: "#94a3b8", fontWeight: 700, whiteSpace: "nowrap" }}>TYPE</th>
                <th style={{ padding: "10px 14px", color: "#94a3b8", fontWeight: 700, whiteSpace: "nowrap" }}>SOURCE ACCOUNT</th>
                <th style={{ padding: "10px 14px", color: "#94a3b8", fontWeight: 700, whiteSpace: "nowrap" }}>DESTINATION ACCOUNT</th>
                <th style={{ padding: "10px 14px", color: "#94a3b8", fontWeight: 700, whiteSpace: "nowrap" }}>HOP #</th>
                <th style={{ padding: "10px 14px", color: "#94a3b8", fontWeight: 700, whiteSpace: "nowrap" }}>RISK SCORE</th>
                <th style={{ padding: "10px 14px", color: "#94a3b8", fontWeight: 700, whiteSpace: "nowrap" }}>STATUS</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: "center", padding: 30, color: "var(--text-muted)" }}>
                    Querying transaction database...
                  </td>
                </tr>
              ) : transactions.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: "center", padding: 30, color: "var(--text-muted)" }}>
                    No transactions match the selected filters.
                  </td>
                </tr>
              ) : (
                transactions.map((tx, idx) => {
                  const isFraud = String(tx.is_fraud) === "1";
                  const isTerminal = tx.transaction_type === "ATM_WITHDRAWAL";
                  const riskVal = parseFloat(tx.ip_risk_score || 0);

                  return (
                    <tr
                      key={tx.transaction_id || idx}
                      style={{
                        borderBottom: "1px solid #162035",
                        background: idx % 2 === 0 ? "transparent" : "rgba(255, 255, 255, 0.015)",
                      }}
                    >
                      <td style={{ padding: "10px 14px", fontFamily: "monospace", color: "#38bdf8", fontWeight: 700, whiteSpace: "nowrap" }}>
                        {tx.transaction_id}
                      </td>
                      <td style={{ padding: "10px 14px", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                        {tx.timestamp}
                      </td>
                      <td style={{ padding: "10px 14px", fontWeight: 700, color: isFraud ? "#f87171" : "var(--text-primary)", whiteSpace: "nowrap" }}>
                        ₹{parseFloat(tx.amount || 0).toLocaleString()}
                      </td>
                      <td style={{ padding: "10px 14px", whiteSpace: "nowrap" }}>
                        <span style={{
                          fontSize: 9,
                          fontWeight: 800,
                          padding: "2px 6px",
                          borderRadius: 3,
                          background: isTerminal ? "rgba(239, 68, 68, 0.2)" : "#1e293b",
                          color: isTerminal ? "#f87171" : "#94a3b8",
                          border: isTerminal ? "1px solid #ef4444" : "1px solid #334155",
                        }}>
                          {tx.transaction_type}
                        </span>
                      </td>
                      <td style={{ padding: "10px 14px", fontFamily: "monospace", color: "var(--text-secondary)", whiteSpace: "nowrap" }}>
                        {tx.source_account} ({tx.source_bank || "BANK"})
                      </td>
                      <td style={{ padding: "10px 14px", fontFamily: "monospace", color: "var(--text-secondary)", whiteSpace: "nowrap" }}>
                        {tx.destination_account} ({tx.destination_bank || "BANK"})
                      </td>
                      <td style={{ padding: "10px 14px", whiteSpace: "nowrap" }}>
                        <span style={{
                          fontSize: 10,
                          fontWeight: 700,
                          padding: "1px 6px",
                          borderRadius: 3,
                          background: parseInt(tx.hop_number || 0) > 1 ? "rgba(245, 158, 11, 0.2)" : "rgba(56, 189, 248, 0.1)",
                          color: parseInt(tx.hop_number || 0) > 1 ? "#fbbf24" : "#38bdf8",
                        }}>
                          Hop {tx.hop_number || 0}
                        </span>
                      </td>
                      <td style={{ padding: "10px 14px", whiteSpace: "nowrap" }}>
                        <span style={{
                          fontSize: 10,
                          fontWeight: 800,
                          color: riskVal >= 0.7 ? "#ef4444" : riskVal >= 0.4 ? "#f59e0b" : "#10b981",
                        }}>
                          {(riskVal * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td style={{ padding: "10px 14px", whiteSpace: "nowrap" }}>
                        <span style={{
                          fontSize: 9,
                          fontWeight: 800,
                          padding: "2px 6px",
                          borderRadius: 3,
                          background: isFraud ? "rgba(239, 68, 68, 0.15)" : "rgba(16, 185, 129, 0.15)",
                          color: isFraud ? "#f87171" : "#34d399",
                          border: isFraud ? "1px solid #ef4444" : "1px solid #10b981",
                        }}>
                          {isFraud ? "FLAGGED FRAUD" : "RETAIL"}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div style={{
          padding: "12px 18px",
          background: "#080d1a",
          borderTop: "1px solid var(--border)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 10,
          flexWrap: "wrap",
        }}>
          <button
            onClick={() => handlePageChange(Math.max(0, page - 1))}
            disabled={page === 0 || loading}
            style={{
              background: "#1e293b",
              border: "1px solid var(--border)",
              color: "var(--text-primary)",
              borderRadius: 4,
              padding: "6px 14px",
              fontSize: 12,
              cursor: page === 0 ? "not-allowed" : "pointer",
              opacity: page === 0 ? 0.5 : 1,
            }}
          >
            ← Previous Page
          </button>

          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
            Showing {page * limit + 1} - {Math.min(totalCount, (page + 1) * limit)} of {totalCount.toLocaleString()}
          </span>

          <button
            onClick={() => handlePageChange(page + 1)}
            disabled={(page + 1) * limit >= totalCount || loading}
            style={{
              background: "#1e293b",
              border: "1px solid var(--border)",
              color: "var(--text-primary)",
              borderRadius: 4,
              padding: "6px 14px",
              fontSize: 12,
              cursor: (page + 1) * limit >= totalCount ? "not-allowed" : "pointer",
              opacity: (page + 1) * limit >= totalCount ? 0.5 : 1,
            }}
          >
            Next Page →
          </button>
        </div>
      </div>
    </div>
  );
}
