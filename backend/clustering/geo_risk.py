"""
backend/clustering/geo_risk.py — Project DRISHTI
==================================================
Geospatial Risk Analysis & GeoJSON Heatmap Density Layer Generator.

Capabilities:
  1. Generates standard RFC 7946 compliant GeoJSON FeatureCollection.
  2. Creates dynamic spatial risk density zones (hex/radial polygons)
     centered around predicted ATM withdrawal clusters and victim coordinates.
  3. Includes ATM candidate nodes with risk intensity values.
  4. Includes nearest police response nodes and connection routes.
  5. Plugs natively into Leaflet / React-Leaflet (<GeoJSON /> layer).
"""

import math
from typing import Dict, Any, List, Optional
from backend.clustering.hotspot import haversine_km

# Helper to generate polygon circle approximation in GeoJSON coords [lon, lat]
def _generate_circle_polygon(center_lat: float, center_lon: float, radius_km: float, num_points: int = 24) -> List[List[float]]:
    coords = []
    # 1 deg lat ≈ 111.32 km, 1 deg lon ≈ 111.32 * cos(lat) km
    lat_deg = radius_km / 111.32
    lon_deg = radius_km / (111.32 * math.cos(math.radians(center_lat)))

    for i in range(num_points):
        angle = (2 * math.pi * i) / num_points
        d_lat = lat_deg * math.sin(angle)
        d_lon = lon_deg * math.cos(angle)
        coords.append([round(center_lon + d_lon, 6), round(center_lat + d_lat, 6)])

    # Close the polygon ring
    coords.append(coords[0])
    return coords


class GeospatialRiskEngine:
    """
    Computes spatial risk density zones and compiles full GeoJSON layer for map display.
    """

    def generate_risk_geojson(
        self,
        victim_lat: Optional[float],
        victim_lon: Optional[float],
        top_k_locations: List[Dict[str, Any]],
        police_unit: Optional[Dict[str, Any]] = None,
        case_risk_score: float = 75.0,
    ) -> Dict[str, Any]:
        """
        Builds a GeoJSON FeatureCollection for real-time risk heatmapping.
        """
        features: List[Dict[str, Any]] = []

        # 1. Primary Risk Hotspot Polygon (Immediate Interception Zone - 500m to 1.5km)
        if top_k_locations:
            primary = top_k_locations[0]
            p_lat, p_lon = primary["lat"], primary["lon"]
            rad_km = primary.get("radius_km", 0.6)

            # High Risk Core Zone
            core_poly = _generate_circle_polygon(p_lat, p_lon, rad_km)
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [core_poly],
                },
                "properties": {
                    "layer_type": "RISK_ZONE",
                    "risk_tier": "CRITICAL",
                    "risk_intensity": round(min(1.0, case_risk_score / 100.0), 2),
                    "fill_color": "#ef4444",
                    "stroke_color": "#b91c1c",
                    "label": f"Primary Withdrawal Interception Zone ({primary['location_name']})",
                    "radius_km": rad_km,
                },
            })

            # Secondary Buffer Zone (1.8x radius)
            outer_poly = _generate_circle_polygon(p_lat, p_lon, rad_km * 1.8)
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [outer_poly],
                },
                "properties": {
                    "layer_type": "BUFFER_ZONE",
                    "risk_tier": "MODERATE",
                    "risk_intensity": round(min(0.7, (case_risk_score / 100.0) * 0.6), 2),
                    "fill_color": "#f97316",
                    "stroke_color": "#c2410c",
                    "label": "Secondary Perimeter & Escape Corridor",
                    "radius_km": round(rad_km * 1.8, 2),
                },
            })

        # 2. Candidate ATM Node Points
        for loc in top_k_locations:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [loc["lon"], loc["lat"]],
                },
                "properties": {
                    "layer_type": "CANDIDATE_ATM",
                    "rank": loc.get("rank", 1),
                    "location_name": loc.get("location_name", "ATM"),
                    "atm_count": loc.get("atm_count", 1),
                    "probability": loc.get("probability", 0.5),
                    "confidence": loc.get("confidence", 0.5),
                    "priority_rank": loc.get("priority_rank", loc.get("rank", 1)),
                    "interception_priority": loc.get("interception_priority", 60.0),
                },
            })

        # 3. Police Response Unit Point & Vector Line to Target
        if police_unit and top_k_locations:
            u_lat = police_unit["unit_lat"]
            u_lon = police_unit["unit_lon"]
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [u_lon, u_lat],
                },
                "properties": {
                    "layer_type": "POLICE_STATION",
                    "unit_id": police_unit["nearest_unit_id"],
                    "unit_name": police_unit["unit_name"],
                    "vehicle": police_unit["unit_vehicle"],
                    "eta_minutes": police_unit["eta_minutes"],
                    "distance_km": police_unit["distance_km"],
                },
            })

            # LineString representing tactical dispatch route
            primary = top_k_locations[0]
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [u_lon, u_lat],
                        [primary["lon"], primary["lat"]],
                    ],
                },
                "properties": {
                    "layer_type": "DISPATCH_ROUTE",
                    "eta_minutes": police_unit["eta_minutes"],
                    "distance_km": police_unit["distance_km"],
                    "status": police_unit["feasibility_status"],
                },
            })

        # 4. Victim Origin Point (if present)
        if victim_lat and victim_lon:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [victim_lon, victim_lat],
                },
                "properties": {
                    "layer_type": "VICTIM_LOCATION",
                    "label": "Victim Incident Origin",
                },
            })

        return {
            "type": "FeatureCollection",
            "metadata": {
                "generated_by": "DRISHTI-GeospatialRiskEngine",
                "risk_score": case_risk_score,
                "candidate_count": len(top_k_locations),
            },
            "features": features,
        }


# Singleton
_geo_risk_engine: Optional[GeospatialRiskEngine] = None

def get_geo_risk_engine() -> GeospatialRiskEngine:
    global _geo_risk_engine
    if _geo_risk_engine is None:
        _geo_risk_engine = GeospatialRiskEngine()
    return _geo_risk_engine
