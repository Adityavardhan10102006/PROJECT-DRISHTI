# backend/routes/maps.py — Project DRISHTI
"""
REST API endpoints for fetching geospatial data required by the interactive map.
Provides GeoJSON FeatureCollections for ATM terminals and Police response units.
"""

import os
import csv
import json
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any

from backend.auth.security import get_current_user

router = APIRouter(prefix="/map", tags=["Map Data"])

# Utility to convert CSV rows to GeoJSON Point features
def _row_to_feature(row: Dict[str, str], lon_key: str = "lon", lat_key: str = "lat") -> Dict[str, Any]:
    try:
        lon = float(row[lon_key])
        lat = float(row[lat_key])
    except (KeyError, ValueError) as exc:
        raise ValueError(f"Invalid coordinate data: {exc}")
    # Preserve original fields as properties
    properties = {k: v for k, v in row.items() if k not in (lon_key, lat_key)}
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": properties,
    }

@router.get("/atms", response_model=Dict[str, Any], summary="GeoJSON of ATM terminals")
def get_atm_geojson(current_user: dict = Depends(get_current_user)):
    """Return a GeoJSON FeatureCollection of all curated ATM terminals.
    The endpoint is protected – only authenticated users may retrieve location data.
    """
    csv_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "data", "hyderabad_atms.csv")
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="ATM dataset not found")
    features: List[Dict[str, Any]] = []
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                features.append(_row_to_feature(row, lon_key="longitude", lat_key="latitude"))
            except ValueError:
                continue
    return {"type": "FeatureCollection", "features": features}

@router.get("/police", response_model=Dict[str, Any], summary="GeoJSON of police response units")
def get_police_geojson(current_user: dict = Depends(get_current_user)):
    """Return a GeoJSON FeatureCollection of police rapid‑response units.
    The source file is `data/police_units.json` which already stores latitude/longitude.
    """
    json_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "data", "police_units.json")
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="Police units dataset not found")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise HTTPException(status_code=500, detail="Police units file format invalid")
    features: List[Dict[str, Any]] = []
    for entry in data:
        try:
            lon = float(entry["lon"])
            lat = float(entry["lat"])
        except (KeyError, ValueError):
            continue
        properties = {k: v for k, v in entry.items() if k not in ("lon", "lat")}
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": properties,
        })
    return {"type": "FeatureCollection", "features": features}
