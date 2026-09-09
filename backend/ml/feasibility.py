"""
backend/ml/feasibility.py — Project DRISHTI
============================================
Police Response Feasibility & Interception Prioritisation Engine.

Capabilities:
  1. Maintains registry of police stations / PCR mobile patrol units
     across major Indian cities.
  2. Finds nearest unit to candidate cash-out locations.
  3. Computes travel ETA based on urban patrol transit dynamics.
  4. Evaluates Interception Time Margin:
       Margin = Peak Withdrawal Time - Police Unit ETA
  5. Computes composite Action Priority Score:
       Priority = 0.6 * Risk Score + 0.4 * (Feasibility Score * 100)
"""

import os
import json
import math
from typing import List, Dict, Any, Optional
from backend.clustering.hotspot import haversine_km

POLICE_DATA_PATH = "data/police_units.json"

def _load_police_registry() -> List[Dict[str, Any]]:
    units = []
    if os.path.exists(POLICE_DATA_PATH):
        try:
            with open(POLICE_DATA_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if loaded and isinstance(loaded, list):
                    units = loaded
        except Exception as e:
            print(f"[DRISHTI] Warning: Could not read {POLICE_DATA_PATH} ({e})")
    if not units:
        units = list(POLICE_UNITS_REGISTRY)

    for u in units:
        if "lat" not in u and "latitude" in u:
            u["lat"] = float(u["latitude"])
        if "lon" not in u and "longitude" in u:
            u["lon"] = float(u["longitude"])
        if "vehicle" not in u:
            u["vehicle"] = "Patrol Interceptor"
    return units

# Realistic police station anchors in major Indian cities
POLICE_UNITS_REGISTRY = [
    # Mumbai
    {"unit_id": "MUM-PCR-01", "name": "Colaba Police Station", "city": "Mumbai", "lat": 18.9150, "lon": 72.8258, "vehicle": "Quick Response Team (QRT)"},
    {"unit_id": "MUM-PCR-02", "name": "Bandra Cyber Cell", "city": "Mumbai", "lat": 19.0596, "lon": 72.8295, "vehicle": "Patrol Van Alpha"},
    {"unit_id": "MUM-PCR-03", "name": "Andheri East Station", "city": "Mumbai", "lat": 19.1136, "lon": 72.8697, "vehicle": "Interceptor Unit 3"},
    {"unit_id": "MUM-PCR-04", "name": "Navi Mumbai Vashi Chowki", "city": "Mumbai", "lat": 19.0771, "lon": 72.9986, "vehicle": "Patrol Van Delta"},
    # Delhi
    {"unit_id": "DEL-PCR-01", "name": "Connaught Place Police Station", "city": "Delhi", "lat": 28.6315, "lon": 77.2167, "vehicle": "PCR Falcon 1"},
    {"unit_id": "DEL-PCR-02", "name": "Hauz Khas Cyber Cell", "city": "Delhi", "lat": 28.5494, "lon": 77.2001, "vehicle": "QRT Bravo"},
    {"unit_id": "DEL-PCR-03", "name": "Rohini Sector 3 PS", "city": "Delhi", "lat": 28.7041, "lon": 77.1025, "vehicle": "Interceptor Unit 7"},
    # Bangalore
    {"unit_id": "BLR-PCR-01", "name": "Koramangala Police Station", "city": "Bangalore", "lat": 12.9352, "lon": 77.6245, "vehicle": "Cheetah Mobile 04"},
    {"unit_id": "BLR-PCR-02", "name": "Indiranagar Cyber Station", "city": "Bangalore", "lat": 12.9784, "lon": 77.6408, "vehicle": "Cheetah Mobile 09"},
    {"unit_id": "BLR-PCR-03", "name": "Whitefield Division Chowki", "city": "Bangalore", "lat": 12.9698, "lon": 77.7500, "vehicle": "QRT Unit 12"},
    # Hyderabad
    {"unit_id": "HYD-PCR-01", "name": "Banjara Hills PS", "city": "Hyderabad", "lat": 17.4156, "lon": 78.4350, "vehicle": "Blue Colts Patrol 1"},
    {"unit_id": "HYD-PCR-02", "name": "Cyberabad Cyber Crime PS", "city": "Hyderabad", "lat": 17.4399, "lon": 78.3800, "vehicle": "Falcon Interceptor"},
    # Kolkata
    {"unit_id": "KOL-PCR-01", "name": "Park Street Police Station", "city": "Kolkata", "lat": 22.5512, "lon": 78.3540, "vehicle": "PCR Radio Flying Squad"},
    # Pune
    {"unit_id": "PUN-PCR-01", "name": "Shivajinagar Police Station", "city": "Pune", "lat": 18.5314, "lon": 73.8446, "vehicle": "Damini Mobile Patrol"},
    # General fallback
    {"unit_id": "GEN-PCR-99", "name": "Central Police Headquarters", "city": "National", "lat": 20.5937, "lon": 78.9629, "vehicle": "Rapid Action Patrol"},
]

# Urban patrol average speed in Indian cities (km/h)
URBAN_PATROL_SPEED_KMH = 28.0
DISPATCH_DELAY_MINUTES = 2.0


class FeasibilityEngine:
    """
    Computes distance, ETA, feasibility score, and interception priority.
    """

    def __init__(self, registry: Optional[List[Dict[str, Any]]] = None):
        self.registry = registry or _load_police_registry()

    def evaluate_location_feasibility(
        self,
        target_lat: float,
        target_lon: float,
        peak_withdrawal_minutes: int,
        case_risk_score: float,
    ) -> Dict[str, Any]:
        """
        Evaluates interception feasibility for a specific candidate location.
        """
        # Find closest police station / unit
        nearest_unit = None
        min_dist = float("inf")

        for unit in self.registry:
            dist = haversine_km(target_lat, target_lon, unit["lat"], unit["lon"])
            if dist < min_dist:
                min_dist = dist
                nearest_unit = unit

        if nearest_unit is None or min_dist > 50.0:
            # If the closest anchor in the national list is > 50km away (e.g. smaller town),
            # synthesize a localized local precinct 2.5 to 5 km away for realistic simulation
            nearest_unit = {
                "unit_id": "LOCAL-PCR-01",
                "name": "Local Police Station (Jurisdiction Precinct)",
                "city": "Local Jurisdiction",
                "lat": round(target_lat + 0.018, 4),
                "lon": round(target_lon + 0.015, 4),
                "vehicle": "Local Patrol Van",
            }
            min_dist = haversine_km(target_lat, target_lon, nearest_unit["lat"], nearest_unit["lon"])

        # Calculate transit ETA
        travel_time = (min_dist / URBAN_PATROL_SPEED_KMH) * 60.0
        eta_minutes = round(travel_time + DISPATCH_DELAY_MINUTES, 1)

        # Margin = peak cash-out time - unit arrival time
        time_margin = round(peak_withdrawal_minutes - eta_minutes, 1)

        # Feasibility score (0.0 to 1.0)
        if time_margin >= 20.0:
            feasibility_score = 0.95
            status = "EXCELLENT_MARGIN"
            desc = f"Unit can intercept {time_margin} min prior to peak cash-out."
        elif time_margin >= 10.0:
            feasibility_score = 0.82
            status = "GOOD_MARGIN"
            desc = f"Interception feasible with {time_margin} min window buffer."
        elif time_margin >= 0.0:
            feasibility_score = 0.58
            status = "TIGHT_MARGIN"
            desc = f"High-velocity response needed: arrival is {abs(time_margin)} min close to peak."
        else:
            feasibility_score = max(0.15, 0.40 + (time_margin / 60.0))
            status = "CRITICAL_DEFICIT"
            desc = f"Unit ETA ({eta_minutes} min) exceeds predicted peak window ({peak_withdrawal_minutes} min)."

        feasibility_score = round(float(feasibility_score), 3)

        # Composite priority: 60% risk, 40% feasibility
        # Prioritizes high risk cases where interception is actually actionable!
        composite_priority = round(0.60 * case_risk_score + 0.40 * (feasibility_score * 100.0), 1)

        return {
            "nearest_unit_id": nearest_unit["unit_id"],
            "unit_name": nearest_unit["name"],
            "unit_vehicle": nearest_unit["vehicle"],
            "unit_lat": nearest_unit["lat"],
            "unit_lon": nearest_unit["lon"],
            "distance_km": round(min_dist, 2),
            "eta_minutes": eta_minutes,
            "peak_withdrawal_minutes": peak_withdrawal_minutes,
            "time_margin_minutes": time_margin,
            "feasibility_score": feasibility_score,
            "feasibility_status": status,
            "feasibility_desc": desc,
            "composite_priority": composite_priority,
        }

    def rank_top_k_candidates(
        self,
        top_k_locations: List[Dict[str, Any]],
        peak_withdrawal_minutes: int,
        case_risk_score: float,
    ) -> List[Dict[str, Any]]:
        """
        Enriches top-K locations with feasibility evaluation and ranks by composite priority.
        """
        enriched = []
        for loc in top_k_locations:
            feas = self.evaluate_location_feasibility(
                target_lat=loc["lat"],
                target_lon=loc["lon"],
                peak_withdrawal_minutes=peak_withdrawal_minutes,
                case_risk_score=case_risk_score,
            )
            item = dict(loc)
            item["feasibility"] = feas
            item["interception_priority"] = feas["composite_priority"]
            enriched.append(item)

        # Sort by composite priority descending
        enriched.sort(key=lambda x: x["interception_priority"], reverse=True)
        for i, item in enumerate(enriched):
            item["priority_rank"] = i + 1

        return enriched


# Singleton
_feasibility_engine_instance: Optional[FeasibilityEngine] = None

def get_feasibility_engine() -> FeasibilityEngine:
    global _feasibility_engine_instance
    if _feasibility_engine_instance is None:
        _feasibility_engine_instance = FeasibilityEngine()
    return _feasibility_engine_instance
