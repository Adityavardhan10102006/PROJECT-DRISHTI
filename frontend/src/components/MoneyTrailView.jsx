import React, { useState, useEffect } from "react";
import { fetchCases, fetchCaseDetail } from "../api.js";

export default function MoneyTrailView({ selectedCaseId }) {
  const [cases, setCases] = useState([]);
  const [activeCaseId, setActiveCaseId] = useState(selectedCaseId || "");
  const [caseDetail, setCaseDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(1);

  useEffect(() => {
    async function loadCasesList() {
      try {
        const cList = await fetchCases({ limit: 50 });
        setCases(cList);
        if (!activeCaseId && cList.length > 0) {
          setActiveCaseId(cList[0].case_id);
        }
      } catch (err) {
        console.error("Failed to load cases:", err);
      }
    }
    loadCasesList();
  }, []);

  useEffect(() => {
    if (!activeCaseId) return;
    async function loadDetail() {
      setLoading(true);
      try {
        const d = await fetchCaseDetail(activeCaseId);
        setCaseDetail(d);
        setSelectedNode(null);
        setSelectedEdge(null);
      } catch (err) {
        console.error("Failed to load case detail:", err);
      } finally {
        setLoading(false);
      }
    }
    loadDetail();
  }, [activeCaseId]);

  const trail = caseDetail?.money_trail || {};
  const hops = trail.hops || [];

  return (
    <div className="money-trail-view-container">
      <div className="trail-view-header">
        <div>
          <h1 className="trail-view-title">NETWORKX MULTI-HOP MONEY TRAIL INVESTIGATOR</h1>
          <p className="trail-view-subtitle">
            Graph traversal, mule syndicate layering analysis, and cash-out terminal interception
          </p>
        </div>

        <div className="case-selector-group">
          <label>Select Case:</label>
          <select
            value={activeCaseId}
            onChange={(e) => setActiveCaseId(e.target.value)}
            className="filter-select font-mono"
          >
            {cases.map((c) => (
              <option key={c.case_id} value={c.case_id}>
                {c.case_id} — ₹{Number(c.amount).toLocaleString("en-IN")} ({c.fraud_type})
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <span>Traversing transaction graph...</span>
        </div>
      ) : (
        <div className="trail-workspace">
          {/* TOP CONTROLS & METRICS */}
          <div className="trail-toolbar">
            <div className="toolbar-stats font-mono">
              <span>Hops: <strong>{hops.length}</strong></span>
              <span>•</span>
              <span>Outflow: <strong>₹{Number(trail.initial_amount || caseDetail?.amount || 0).toLocaleString("en-IN")}</strong></span>
              <span>•</span>
              <span>Cash-Out Terminal: <strong className="text-amber">₹{Number(trail.final_cashout_amount || caseDetail?.amount || 0).toLocaleString("en-IN")}</strong></span>
              <span>•</span>
              <span>Graph Density: <strong>{((trail.graph_metrics?.max_betweenness || 0.12) * 100).toFixed(1)}%</strong></span>
            </div>

            <div className="zoom-controls">
              <button onClick={() => setZoomLevel((z) => Math.max(0.7, z - 0.15))} title="Zoom Out">🔍−</button>
              <span className="font-mono text-muted">{Math.round(zoomLevel * 100)}%</span>
              <button onClick={() => setZoomLevel((z) => Math.min(1.5, z + 0.15))} title="Zoom In">🔍+</button>
              <button onClick={() => setZoomLevel(1)} title="Reset Zoom">Reset</button>
            </div>
          </div>

          {/* INTERACTIVE GRAPH CANVAS */}
          <div className="trail-canvas-area" style={{ transform: `scale(${zoomLevel})`, transformOrigin: "top left" }}>
            {hops.length === 0 ? (
              <div className="empty-state">No multi-hop laundering sequence detected.</div>
            ) : (
              <div className="network-flow-row">
                {/* Victim Node */}
                <div
                  className={`network-node-box victim-node-box ${selectedNode?.id === "victim" ? "selected-node" : ""}`}
                  onClick={() => {
                    setSelectedEdge(null);
                    setSelectedNode({
                      id: "victim",
                      role: "Victim Account",
                      account: caseDetail?.origin_account || "ACC-VICTIM-01",
                      first_seen: "T0 (Incident Trigger)",
                      last_seen: "T0",
                      total_volume: caseDetail?.amount,
                      risk_indicator: "SOURCE_COMPLAINANT",
                      bank: "Victim Originating Bank",
                    });
                  }}
                >
                  <div className="node-badge">VICTIM SOURCE</div>
                  <div className="node-icon">👤</div>
                  <div className="node-account font-mono">{caseDetail?.origin_account || "ACC-VICTIM-01"}</div>
                  <div className="node-sub">Outflow: ₹{Number(caseDetail?.amount || 0).toLocaleString("en-IN")}</div>
                </div>

                {/* Hops & Intermediary Mule Nodes */}
                {hops.map((hop, idx) => (
                  <React.Fragment key={idx}>
                    {/* Edge */}
                    <div
                      className={`network-edge-connector ${selectedEdge?.hop_index === hop.hop_index ? "selected-edge" : ""}`}
                      onClick={() => {
                        setSelectedNode(null);
                        setSelectedEdge({
                          hop_index: hop.hop_index || idx + 1,
                          from_account: hop.from_account,
                          to_account: hop.to_account,
                          amount: hop.amount,
                          txn_type: hop.txn_type || "IMPS/UPI",
                          minutes: hop.minutes_from_start,
                          commission: hop.commission_retained,
                          ref: hop.txn_ref || `TXN-REF-00${idx + 1}`,
                        });
                      }}
                    >
                      <div className="edge-line">
                        <span className="edge-arrow">▶</span>
                      </div>
                      <div className="edge-label font-mono">
                        <span>₹{Number(hop.amount).toLocaleString("en-IN")}</span>
                        <span className="edge-time">+{hop.minutes_from_start}m</span>
                      </div>
                    </div>

                    {/* Target Node */}
                    <div
                      className={`network-node-box ${
                        hop.is_terminal_cashout ? "terminal-node-box" : "mule-node-box"
                      } ${selectedNode?.id === hop.to_account ? "selected-node" : ""}`}
                      onClick={() => {
                        setSelectedEdge(null);
                        setSelectedNode({
                          id: hop.to_account,
                          role: hop.is_terminal_cashout ? "ATM Cash-Out Kiosk" : `Layer ${idx + 1} Mule Account`,
                          account: hop.to_account,
                          first_seen: `+${hop.minutes_from_start} min`,
                          last_seen: `+${hop.minutes_from_start} min`,
                          total_volume: hop.amount,
                          risk_indicator: hop.is_terminal_cashout ? "TERMINAL_WITHDRAWAL" : "LAYERED_TRANSFER",
                          bank: hop.to_bank || "Partner Bank",
                          ifsc: hop.to_ifsc || "BANK0001234",
                        });
                      }}
                    >
                      <div className="node-badge">
                        {hop.is_terminal_cashout ? "🎯 CASH-OUT TERMINAL" : `MULE LAYER ${idx + 1}`}
                      </div>
                      <div className="node-icon">{hop.is_terminal_cashout ? "🏧" : "🔄"}</div>
                      <div className="node-account font-mono">{hop.to_account}</div>
                      <div className="node-sub">
                        {hop.is_terminal_cashout ? "Kiosk Withdrawal" : `Received: ₹${Number(hop.amount).toLocaleString("en-IN")}`}
                      </div>
                    </div>
                  </React.Fragment>
                ))}
              </div>
            )}
          </div>

          {/* INSPECTION DRAWER */}
          <div className="trail-inspector-panel">
            {selectedNode ? (
              <div className="inspector-card">
                <h3>NODE INTELLIGENCE: {selectedNode.role}</h3>
                <div className="inspector-grid font-mono">
                  <div>Account Identifier (Masked): <strong>{selectedNode.account}</strong></div>
                  <div>Entity Type: <strong>{selectedNode.role}</strong></div>
                  <div>First Seen: <strong>{selectedNode.first_seen}</strong></div>
                  <div>Last Seen: <strong>{selectedNode.last_seen}</strong></div>
                  <div>Total Volume Handled: <strong className="text-amber">₹{Number(selectedNode.total_volume || 0).toLocaleString("en-IN")}</strong></div>
                  <div>Risk Signal: <strong className="text-red">{selectedNode.risk_indicator}</strong></div>
                  <div>Bank Institution: <strong>{selectedNode.bank}</strong></div>
                </div>
                <div className="inspector-hint">
                  Recommendation: Section 91 CrPC freeze directive should be issued for this intermediary node.
                </div>
              </div>
            ) : selectedEdge ? (
              <div className="inspector-card">
                <h3>TRANSACTION EDGE: HOP #{selectedEdge.hop_index}</h3>
                <div className="inspector-grid font-mono">
                  <div>Transfer Reference: <strong>{selectedEdge.ref}</strong></div>
                  <div>Channel / Type: <strong>{selectedEdge.txn_type}</strong></div>
                  <div>Source Account: <strong>{selectedEdge.from_account}</strong></div>
                  <div>Target Account: <strong>{selectedEdge.to_account}</strong></div>
                  <div>Transfer Amount: <strong className="text-cyan">₹{Number(selectedEdge.amount).toLocaleString("en-IN")}</strong></div>
                  <div>Latency from Incident: <strong>+{selectedEdge.minutes} minutes</strong></div>
                  <div>Commission Retained: <strong>₹{selectedEdge.commission || 0}</strong></div>
                </div>
              </div>
            ) : (
              <div className="inspector-placeholder font-mono text-muted">
                ℹ️ Click on any node or transfer edge above to inspect forensic transaction telemetry and bank routing details.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
