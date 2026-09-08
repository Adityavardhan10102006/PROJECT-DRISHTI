/**
 * src/components/MoneyTrailFlow.jsx — Project DRISHTI
 * Multi-Hop Mule Account Money Trail Visualizer.
 *
 * Renders the laundering transaction graph as an intuitive visual flow:
 * Victim -> Mule 1 -> Mule 2 -> Terminal ATM Cash-Out
 * With hop-by-hop latency, transaction amounts, and laundering cuts.
 */

function formatINR(val) {
  if (val === undefined || val === null) return "—";
  return "Rs " + Math.round(Number(val)).toLocaleString("en-IN");
}

export default function MoneyTrailFlow({ moneyTrail }) {
  if (!moneyTrail || !moneyTrail.hops || moneyTrail.hops.length === 0) {
    return (
      <div className="empty-trail-state">
        <span className="empty-icon">⛓️</span>
        <div className="empty-title">No Multi-Hop Trail Available</div>
        <div className="empty-desc">
          Single direct transaction or insufficient transaction telemetry.
        </div>
      </div>
    );
  }

  const {
    starting_account,
    initial_amount,
    final_cashout_amount,
    hop_count,
    trail_duration_minutes,
    hops,
    graph_metrics = {},
  } = moneyTrail;

  const totalFeePct = initial_amount > 0
    ? Math.round(((initial_amount - final_cashout_amount) / initial_amount) * 100)
    : 0;

  return (
    <div className="trail-flow-wrapper">
      {/* ── Trail Metrics Strip ── */}
      <div className="trail-metrics-bar">
        <div className="trail-metric-box">
          <span className="t-label">Victim Outflow</span>
          <span className="t-val text-red">{formatINR(initial_amount)}</span>
        </div>
        <div className="trail-metric-box">
          <span className="t-label">ATM Cash-Out</span>
          <span className="t-val text-yellow">{formatINR(final_cashout_amount)}</span>
        </div>
        <div className="trail-metric-box">
          <span className="t-label">Laundering Cut</span>
          <span className="t-val text-orange">
            {totalFeePct}% ({formatINR(initial_amount - final_cashout_amount)})
          </span>
        </div>
        <div className="trail-metric-box">
          <span className="t-label">Diversion Velocity</span>
          <span className="t-val text-cyan">{trail_duration_minutes || (hop_count * 10)} mins</span>
        </div>
      </div>

      {/* ── Visual Flow Diagram ── */}
      <div className="flow-diagram-container">
        {/* Victim Source Node */}
        <div className="flow-node-card victim-node">
          <div className="flow-node-badge badge-victim">VICTIM ACCOUNT</div>
          <div className="flow-node-main">
            <span className="node-avatar">👤</span>
            <div>
              <div className="flow-node-title">Victim Source</div>
              <div className="flow-node-acc mono">{starting_account || "ACC-VICTIM-01"}</div>
            </div>
          </div>
          <div className="flow-node-amount">
            Initial Debit: <strong>{formatINR(initial_amount)}</strong>
          </div>
        </div>

        {/* Hops & Mule Nodes */}
        {hops.map((hop, idx) => (
          <div key={idx} className="flow-step">
            {/* Connecting Transfer Vector */}
            <div className="flow-connector">
              <div className="connector-line">
                <div className="connector-pulse"></div>
              </div>
              <div className="connector-details">
                <span className="transfer-pill">
                  {hop.txn_type || "IMPS"} · {formatINR(hop.amount)}
                </span>
                <span className="transfer-time">
                  +{hop.minutes_from_start || (idx + 1) * 8}m
                  {hop.fee_deducted ? ` · -${formatINR(hop.fee_deducted)} fee` : ""}
                </span>
              </div>
            </div>

            {/* Target Node */}
            <div
              className={`flow-node-card ${
                hop.is_terminal_cashout ? "terminal-node" : "mule-node"
              }`}
            >
              <div
                className={`flow-node-badge ${
                  hop.is_terminal_cashout ? "badge-terminal" : "badge-mule"
                }`}
              >
                {hop.is_terminal_cashout
                  ? "🎯 TERMINAL CASHOUT POINT"
                  : `LAYER ${hop.hop_index} MULE ACCOUNT`}
              </div>

              <div className="flow-node-main">
                <span className="node-avatar">
                  {hop.is_terminal_cashout ? "🏧" : "🔄"}
                </span>
                <div>
                  <div className="flow-node-title">
                    {hop.is_terminal_cashout
                      ? "ATM Withdrawal Point"
                      : (hop.to_bank || "Beneficiary Bank")}
                  </div>
                  <div className="flow-node-acc mono">{hop.to_account}</div>
                </div>
              </div>

              <div className="flow-node-amount">
                {hop.is_terminal_cashout ? (
                  <span className="terminal-cash-text">
                    Cash Withdrawn: <strong>{formatINR(hop.amount)}</strong>
                  </span>
                ) : (
                  <span>
                    Received: <strong>{formatINR(hop.amount)}</strong>
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* ── Graph Centrality Insight ── */}
      {graph_metrics && (
        <div className="graph-insight-footer">
          <span className="insight-tag">
            Network Centrality: <strong>{((graph_metrics.max_betweenness || 0.05) * 100).toFixed(1)}%</strong>
          </span>
          <span className="insight-divider">|</span>
          <span className="insight-note">
            High betweenness indicates syndicated mule aggregation node flagged for freezing under Section 91 CrPC.
          </span>
        </div>
      )}
    </div>
  );
}
