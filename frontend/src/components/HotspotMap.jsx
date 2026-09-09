/**
 * src/components/HotspotMap.jsx — Project DRISHTI
 * Interactive Leaflet Map with Geospatial Risk Heatmap Layer,
 * Top-K Candidate Cash-Out Hotspots, Tactical Police Dispatch Route,
 * Risk Intensity Legend, Marker Clustering, and View-Control Toggle.
 */

import { useState, useEffect, useMemo } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Circle,
  Polyline,
  Popup,
  GeoJSON,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet.markercluster";
import { createPathComponent, createElementObject, extendContext } from "@react-leaflet/core";

// Cluster & Leaflet styles
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";

// React 18 Compatible MarkerClusterGroup Component
const MarkerClusterGroup = createPathComponent((props, context) => {
  const { children, ...options } = props;
  const clusterGroup = new L.MarkerClusterGroup(options);
  return createElementObject(
    clusterGroup,
    extendContext(context, { layerContainer: clusterGroup })
  );
});

// Fix Leaflet default icon paths
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon   from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl:       markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl:     markerShadow,
});

// ── Custom Map DivIcons ─────────────────────────────────────────

// Primary #1 Hotspot Pulsing Icon (ONLY FOR P1 CRITICAL ALERTS)
const HOTSPOT_PULSING_ICON = L.divIcon({
  className: "",
  html: `<div class="pulse-container primary-hotspot">
           <div class="pulse-ring"></div>
           <div class="pulse-dot rank-1">1</div>
         </div>`,
  iconSize:   [30, 30],
  iconAnchor: [15, 15],
  popupAnchor:[0, -15],
});

// Primary #1 Static Icon (FOR P2 and P3 ALERTS - Static without pulse ring)
const HOTSPOT_STATIC_ICON = L.divIcon({
  className: "",
  html: `<div class="pulse-container primary-hotspot static-marker">
           <div class="pulse-dot rank-1" style="box-shadow: none;">1</div>
         </div>`,
  iconSize:   [26, 26],
  iconAnchor: [13, 13],
  popupAnchor:[0, -13],
});

// Candidate #2 / #3 Static Icons
function createCandidateIcon(rank) {
  return L.divIcon({
    className: "",
    html: `<div class="candidate-marker rank-${rank}">
             <span>#${rank}</span>
           </div>`,
    iconSize:   [24, 24],
    iconAnchor: [12, 12],
    popupAnchor:[0, -12],
  });
}

// Police Patrol Van Icon
const POLICE_ICON = L.divIcon({
  className: "",
  html: `<div class="police-marker-pin">
           <span>🚔</span>
         </div>`,
  iconSize:   [28, 28],
  iconAnchor: [14, 14],
  popupAnchor:[0, -14],
});

// Victim Location Icon
const VICTIM_ICON = L.divIcon({
  className: "",
  html: `<div class="victim-marker-pin">
           <span>👤</span>
         </div>`,
  iconSize:   [24, 24],
  iconAnchor: [12, 12],
  popupAnchor:[0, -12],
});

// ── Priority Helper ─────────────────────────────────────────────
function getAlertPriority(pred) {
  if (!pred) return { isCritical: false, isP2: false, isP3: true, label: "P3 · ROUTINE", priorityScore: 30 };
  const effectiveRiskScore = pred.risk_score !== undefined ? Math.round(pred.risk_score) : 65;
  const compositePriority = pred.feasibility?.composite_priority
    ? Math.round(pred.feasibility.composite_priority)
    : (pred.compositePriority !== undefined ? pred.compositePriority : effectiveRiskScore);

  const isCritical =
    compositePriority >= 75 ||
    pred.risk_tier === "CRITICAL" ||
    pred.alert_level === "CRITICAL";

  const isP2 = !isCritical && (
    compositePriority >= 45 ||
    pred.risk_tier === "HIGH" ||
    pred.risk_tier === "MEDIUM"
  );

  const isP3 = !isCritical && !isP2;

  return {
    isCritical,
    isP2,
    isP3,
    label: isCritical ? "P1 · CRITICAL" : (isP2 ? "P2 · ELEVATED" : "P3 · ROUTINE"),
    priorityScore: compositePriority,
  };
}

// ── Auto-pan & FlyTo Helper ────────────────────────────────────
function MapController({ prediction, activeTarget }) {
  const map = useMap();

  useEffect(() => {
    if (activeTarget?.lat && activeTarget?.lon) {
      map.flyTo([activeTarget.lat, activeTarget.lon], 15, {
        duration: 1.2,
        easeLinearity: 0.3,
      });
      return;
    }

    if (!prediction) return;
    const target = prediction.top_k_locations?.[0] || prediction.hotspot;
    if (target?.lat && target?.lon) {
      map.flyTo([target.lat, target.lon], 14, {
        duration: 1.2,
        easeLinearity: 0.35,
      });
    }
  }, [prediction, activeTarget, map]);

  return null;
}

export default function HotspotMap({
  prediction,
  predictions = [],
  activeTarget,
  center = [20.5937, 78.9629],
  onSelectCandidate,
}) {
  const [showHeatmap, setShowHeatmap] = useState(true);
  // View-control toggle: "critical" (default: Top 10 P1 critical alerts) vs "all"
  const [filterMode, setFilterMode] = useState("critical");

  // Pool of all alerts/predictions
  const allAlerts = useMemo(() => {
    if (predictions && predictions.length > 0) return predictions;
    if (prediction) return [prediction];
    return [];
  }, [predictions, prediction]);

  // Filtered alerts based on the View Toggle (Default: Critical Only - Top 10)
  const displayedAlerts = useMemo(() => {
    if (filterMode === "critical") {
      const critical = allAlerts
        .filter(p => getAlertPriority(p).isCritical)
        .sort((a, b) => getAlertPriority(b).priorityScore - getAlertPriority(a).priorityScore)
        .slice(0, 10);
      // If none strictly labeled critical yet, fallback to top scored alerts up to 10
      return critical.length > 0 ? critical : allAlerts.slice(0, 10);
    }
    return allAlerts;
  }, [allAlerts, filterMode]);

  // Active focused prediction details (for radar, dispatch route, and GeoJSON)
  const focusedPrediction = prediction || displayedAlerts[0] || null;
  const topK = focusedPrediction?.top_k_locations || (focusedPrediction?.hotspot ? [focusedPrediction.hotspot] : []);
  const primaryCandidate = topK[0] || focusedPrediction?.hotspot;
  const feasibility = focusedPrediction?.feasibility;
  const nlpEntities = focusedPrediction?.nlp_entities || {};
  const geojsonLayer = focusedPrediction?.geojson_risk_layer;

  // Police dispatch route line coordinates
  const dispatchRoute = (feasibility && primaryCandidate)
    ? [
        [feasibility.unit_lat, feasibility.unit_lon],
        [primaryCandidate.lat, primaryCandidate.lon],
      ]
    : null;

  return (
    <div className="map-wrapper-relative">
      {/* ── Floating Map Top Controls ── */}
      <div className="map-floating-controls">
        <button
          type="button"
          className={`map-ctrl-btn ${showHeatmap ? "active" : ""}`}
          onClick={() => setShowHeatmap(prev => !prev)}
          title="Toggle Geospatial Risk Heatmap Layer"
        >
          {showHeatmap ? "🔥 Risk Heatmap: ON" : "⚪ Heatmap: OFF"}
        </button>

        {focusedPrediction && (
          <span className="map-active-badge">
            Target: {primaryCandidate?.location_name || "ATM Cluster"} ({focusedPrediction.complaint_id || "Active"})
          </span>
        )}
      </div>

      {/* ── Leaflet Map Container ── */}
      <MapContainer
        center={center}
        zoom={5}
        className="map-container"
        zoomControl={true}
        attributionControl={true}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          maxZoom={19}
        />

        <MapController prediction={focusedPrediction} activeTarget={activeTarget} />

        {/* ── 1. Geospatial Risk Heatmap Layer (Focused Case) ── */}
        {showHeatmap && topK.map((loc, i) => {
          const rank = loc.rank || i + 1;
          const prob = loc.probability || loc.confidence || 0.5;
          const rad = (loc.radius_km || 0.6) * 1000;

          return (
            <div key={`heatmap-rings-${i}`}>
              {/* Core High-Density Zone */}
              <Circle
                center={[loc.lat, loc.lon]}
                radius={rad}
                pathOptions={{
                  color: rank === 1 ? "#ef4444" : "#f97316",
                  fillColor: rank === 1 ? "#ef4444" : "#f97316",
                  fillOpacity: rank === 1 ? 0.28 : 0.18,
                  weight: 2,
                  dashArray: rank === 1 ? "4 4" : "6 6",
                }}
              />

              {/* Outer Dispersion Corridor */}
              <Circle
                center={[loc.lat, loc.lon]}
                radius={rad * 1.9}
                pathOptions={{
                  color: rank === 1 ? "#f97316" : "#eab308",
                  fillColor: rank === 1 ? "#f97316" : "#eab308",
                  fillOpacity: 0.10 * prob,
                  weight: 1,
                  dashArray: "8 6",
                }}
              />

              {/* Ambient Risk Aura */}
              <Circle
                center={[loc.lat, loc.lon]}
                radius={rad * 3.0}
                pathOptions={{
                  color: "#38bdf8",
                  fillColor: "#38bdf8",
                  fillOpacity: 0.04,
                  weight: 1,
                  dashArray: "10 8",
                }}
              />
            </div>
          );
        })}

        {/* ── 2. GeoJSON Risk Polygon Feature Rendering ── */}
        {showHeatmap && geojsonLayer && (
          <GeoJSON
            key={`geojson-${focusedPrediction?.complaint_id}-${showHeatmap}`}
            data={geojsonLayer}
            style={(feature) => {
              const props = feature?.properties || {};
              if (props.layer_type === "RISK_ZONE") {
                return {
                  color: props.stroke_color || "#b91c1c",
                  fillColor: props.fill_color || "#ef4444",
                  fillOpacity: 0.22,
                  weight: 2,
                  dashArray: "4 4",
                };
              }
              if (props.layer_type === "BUFFER_ZONE") {
                return {
                  color: props.stroke_color || "#c2410c",
                  fillColor: props.fill_color || "#f97316",
                  fillOpacity: 0.12,
                  weight: 1.5,
                  dashArray: "6 6",
                };
              }
              return { opacity: 0, fillOpacity: 0 };
            }}
          />
        )}

        {/* ── 3. Victim Origin Marker ── */}
        {nlpEntities["inferred_city"] && primaryCandidate && (
          <Marker
            position={[primaryCandidate.lat - 0.009, primaryCandidate.lon - 0.008]}
            icon={VICTIM_ICON}
          >
            <Popup className="drishti-popup">
              <strong style={{ color: "#38bdf8" }}>Victim Origin</strong>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>
                City: {nlpEntities["inferred_city"]}
              </div>
              <div style={{ fontSize: "10px", color: "#cbd5e1", marginTop: 4 }}>
                Incident reported here; fund diversion initiated.
              </div>
            </Popup>
          </Marker>
        )}

        {/* ── 4. Clustered ATM Candidate Markers ── */}
        {/* Requirement 1: Wrap all ATM candidate markers inside MarkerClusterGroup */}
        <MarkerClusterGroup
          chunkedLoading
          spiderfyOnMaxZoom={true}
          showCoverageOnHover={false}
          maxClusterRadius={45}
        >
          {displayedAlerts.flatMap((pred) => {
            const priority = getAlertPriority(pred);
            const candidates = pred.top_k_locations || (pred.hotspot ? [pred.hotspot] : []);

            return candidates.map((loc, idx) => {
              const rank = loc.rank || idx + 1;
              const isPrimary = rank === 1;
              const prob = Math.round((loc.probability || loc.confidence || 0.5) * 100);

              // Requirement 3: Only apply pulsing animation to P1 (Critical) alerts.
              // For P2 and P3, show static markers without pulse-ring.
              const icon = isPrimary
                ? (priority.isCritical ? HOTSPOT_PULSING_ICON : HOTSPOT_STATIC_ICON)
                : createCandidateIcon(rank);

              return (
                <Marker
                  key={`atm-${pred.complaint_id || "alert"}-${rank}-${loc.lat}-${loc.lon}`}
                  position={[loc.lat, loc.lon]}
                  icon={icon}
                  eventHandlers={{
                    click: () => onSelectCandidate?.(loc),
                  }}
                >
                  <Popup className="drishti-popup">
                    <div style={{ minWidth: 230 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                        <span style={{
                          fontSize: "10px",
                          fontWeight: 700,
                          padding: "1px 6px",
                          borderRadius: "3px",
                          background: priority.isCritical ? "rgba(239, 68, 68, 0.2)" : "rgba(56, 189, 248, 0.2)",
                          color: priority.isCritical ? "#f87171" : "#38bdf8",
                          border: `1px solid ${priority.isCritical ? "rgba(239,68,68,0.4)" : "rgba(56,189,248,0.4)"}`,
                          letterSpacing: "0.5px"
                        }}>
                          {priority.label}
                        </span>
                        {pred.complaint_id && (
                          <span style={{ fontSize: "10px", color: "#94a3b8", fontFamily: "monospace" }}>
                            {pred.complaint_id}
                          </span>
                        )}
                      </div>

                      <div style={{
                        fontFamily: "Rajdhani, sans-serif",
                        fontSize: "14px",
                        fontWeight: 700,
                        letterSpacing: "0.5px",
                        color: isPrimary ? (priority.isCritical ? "#ef4444" : "#f97316") : "#38bdf8",
                        marginBottom: 4,
                      }}>
                        Candidate #{rank}: {loc.location_name || "ATM Withdrawal Cluster"}
                      </div>

                      <div style={{ fontSize: "12px", color: "#facc15", fontWeight: 600, marginBottom: 4 }}>
                        Withdrawal Probability: {prob}%
                      </div>

                      {loc.atm_count && (
                        <div style={{ fontSize: "11px", color: "#94a3b8", marginBottom: 2 }}>
                          ATMs in Cluster: <strong style={{ color: "#f1f5f9" }}>{loc.atm_count}</strong>
                        </div>
                      )}

                      {loc.distance_km && (
                        <div style={{ fontSize: "11px", color: "#94a3b8", marginBottom: 2 }}>
                          Distance from Victim: <strong style={{ color: "#f1f5f9" }}>{loc.distance_km} km</strong>
                        </div>
                      )}

                      {loc.interception_priority && (
                        <div style={{ fontSize: "11px", color: "#94a3b8", marginBottom: 2 }}>
                          Tactical Priority: <strong style={{ color: "#4ade80" }}>{loc.interception_priority}/100</strong>
                        </div>
                      )}

                      <div style={{ fontSize: "10px", color: "#64748b", marginTop: 6, paddingTop: 4, borderTop: "1px solid #334155" }}>
                        Lat/Lon: {Number(loc.lat).toFixed(5)}, {Number(loc.lon).toFixed(5)}
                      </div>
                    </div>
                  </Popup>
                </Marker>
              );
            });
          })}
        </MarkerClusterGroup>

        {/* ── 5. Police Patrol Station & Tactical Dispatch Route ── */}
        {feasibility && (
          <>
            <Marker
              position={[feasibility.unit_lat, feasibility.unit_lon]}
              icon={POLICE_ICON}
            >
              <Popup className="drishti-popup">
                <div style={{ minWidth: 200 }}>
                  <div style={{ fontWeight: 700, color: "#38bdf8", fontSize: "13px" }}>
                    {feasibility.unit_name}
                  </div>
                  <div style={{ fontSize: "11px", color: "#cbd5e1", marginTop: 2 }}>
                    Vehicle: {feasibility.unit_vehicle}
                  </div>
                  <div style={{ fontSize: "11px", color: "#4ade80", marginTop: 3 }}>
                    Dispatch ETA: <strong>{feasibility.eta_minutes} mins</strong> ({feasibility.distance_km} km away)
                  </div>
                  <div style={{ fontSize: "11px", color: "#facc15", marginTop: 2 }}>
                    Time Margin: <strong>{feasibility.time_margin_minutes > 0 ? `+${feasibility.time_margin_minutes}` : feasibility.time_margin_minutes} mins</strong>
                  </div>
                  <div style={{ fontSize: "10px", color: "#94a3b8", marginTop: 4 }}>
                    {feasibility.feasibility_desc}
                  </div>
                </div>
              </Popup>
            </Marker>

            {/* Tactical Dispatch Vector Polyline */}
            {dispatchRoute && (
              <Polyline
                positions={dispatchRoute}
                pathOptions={{
                  color: "#38bdf8",
                  weight: 3,
                  dashArray: "8 6",
                  opacity: 0.85,
                }}
              />
            )}
          </>
        )}
      </MapContainer>

      {/* ── Floating Risk Density Legend ── */}
      <div className="map-risk-legend">
        <div className="legend-title">Geospatial Risk Density Scale</div>
        <div className="legend-bar-container">
          <div className="legend-gradient-bar"></div>
          <div className="legend-scale-labels">
            <span>0 Low</span>
            <span>30 Med</span>
            <span>70 High</span>
            <span>100 Critical</span>
          </div>
        </div>
        <div className="legend-markers-list">
          <div className="legend-item">
            <span className="legend-dot dot-core"></span>
            <span>Core Withdrawal Zone (500m)</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot dot-buffer"></span>
            <span>Escape Perimeter (1.5km)</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot dot-route"></span>
            <span>Police Dispatch Route (ETA)</span>
          </div>
        </div>

        {/* ── Requirement 2: View-Control Toggle Switch in Legend ── */}
        <div className="legend-toggle-section">
          <div className="legend-toggle-label">
            <span className="legend-toggle-title">View Mode</span>
            <span className="legend-toggle-status">
              {filterMode === "critical" ? "Critical Only (Top 10)" : "All Alerts"}
            </span>
          </div>
          <div className="view-toggle-btn-group" role="group" aria-label="Map alert view filter">
            <button
              type="button"
              className={`view-toggle-btn ${filterMode === "critical" ? "active" : ""}`}
              onClick={() => setFilterMode("critical")}
              title="Show critical alerts only (Top 10)"
            >
              ⚡ Critical Only (Top 10)
            </button>
            <button
              type="button"
              className={`view-toggle-btn all-btn ${filterMode === "all" ? "active" : ""}`}
              onClick={() => setFilterMode("all")}
              title="Show all alerts"
            >
              🌐 Show All Alerts
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
