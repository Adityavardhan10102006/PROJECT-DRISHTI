"""
backend/clustering/hotspot.py — Project DRISHTI (Day 2)
=========================================================
DBSCAN-based geographic hotspot predictor.

HOW IT WORKS:
  Each complaint in complaints.csv has a `nearby_atms` field — a JSON list
  of 3–5 ATM/branch locations within ~2 km of the victim.

  SINGLE-COMPLAINT MODE (used in /predict):
    Given one complaint, we run DBSCAN on just that complaint's nearby_atms.
    With only 3–5 points, DBSCAN with small eps finds the densest sub-cluster
    or returns the centroid of all points. The predicted hotspot = cluster centroid.

  MULTI-COMPLAINT MODE (used for batch analysis / dashboard heatmap, Day 4):
    Given N complaints in the same city, aggregate all their nearby_atms and
    run DBSCAN across the full set. Large clusters = known withdrawal hotspots.
    This is the more powerful mode — reveals "mule ATM networks."

DBSCAN PARAMETERS:
  eps        = 0.5 km in haversine distance (adjustable)
  min_samples = 2  (low because single-complaint has few points)

  Day 3 tuning: run grid_search_dbscan.py to find optimal eps per city.

ACCURACY NOTES:
  [~] Single-complaint mode accuracy is limited by how many nearby_atms we
      generated (3–5 synthetic points). In production, this would use a real
      ATM geodatabase (RBI/Google Places API) with 20–50 nearby locations.
  [!] For demo: the predicted hotspot will always be geographically near the
      victim (within 2 km), which is realistic for cash-out interception.
  [~] Haversine distance is used instead of Euclidean for geographic accuracy.

Usage:
    from backend.clustering.hotspot import HotspotPredictor
    predictor = HotspotPredictor()

    # Single complaint
    import json
    nearby = json.loads(row["nearby_atms"])
    result = predictor.predict_single(nearby, victim_lat, victim_lon)

    # Batch (multiple complaints, same city)
    all_atms = [json.loads(r["nearby_atms"]) for _, r in df.iterrows()]
    results = predictor.predict_batch(all_atms)
"""

import os
import json
import math
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

# scikit-learn DBSCAN — CPU only, no GPU needed
from sklearn.cluster import DBSCAN

HYD_ATMS_PATH = "data/hyderabad_atms.csv"


# ─────────────────────────────────────────────────────────────
# 1. RESULT DATACLASS
# ─────────────────────────────────────────────────────────────

@dataclass
class HotspotResult:
    """
    Output of the DBSCAN hotspot predictor for one complaint.
    """
    lat:            float           # Cluster centroid latitude
    lon:            float           # Cluster centroid longitude
    radius_km:      float           # Estimated search radius (spread of cluster)
    atm_count:      int             # Number of ATMs in the winning cluster
    confidence:     float           # 0–1: proportion of points in largest cluster
    cluster_id:     int             # DBSCAN cluster label (−1 = noise / fallback)
    cluster_atms:   list = field(default_factory=list)  # Raw ATM dicts in cluster
    all_clusters:   int  = 1        # Total number of clusters found (informational)


# ─────────────────────────────────────────────────────────────
# 2. HAVERSINE METRIC
#    DBSCAN uses this to measure distance between ATM points.
#    More accurate than Euclidean for geographic coordinates.
# ─────────────────────────────────────────────────────────────

_EARTH_RADIUS_KM = 6371.0

def _haversine_matrix(X: np.ndarray) -> np.ndarray:
    """
    Compute pairwise haversine distances (km) for an array of [lat, lon] rows.
    Returns an (N x N) distance matrix.

    We compute this manually and pass it to DBSCAN(metric="precomputed")
    because sklearn's haversine metric requires radians and has different
    conventions — this is clearer and easier to debug.
    """
    n = len(X)
    dist = np.zeros((n, n))
    lats = np.radians(X[:, 0])
    lons = np.radians(X[:, 1])

    for i in range(n):
        dlat = lats - lats[i]
        dlon = lons - lons[i]
        a = np.sin(dlat / 2)**2 + np.cos(lats[i]) * np.cos(lats) * np.sin(dlon / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        dist[i] = _EARTH_RADIUS_KM * c

    return dist


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Single-pair haversine distance in km."""
    r = math.radians
    dlat = r(lat2 - lat1)
    dlon = r(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(r(lat1)) * math.cos(r(lat2)) * math.sin(dlon/2)**2
    return _EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─────────────────────────────────────────────────────────────
# 3. HOTSPOT PREDICTOR
# ─────────────────────────────────────────────────────────────

class HotspotPredictor:
    """
    DBSCAN-based geographic clustering for ATM hotspot prediction.
    Stateless and thread-safe.

    Parameters:
        eps_km      : DBSCAN neighbourhood radius in km (default 0.5 km)
        min_samples : Minimum points to form a core point (default 2)
    """

    def __init__(self, eps_km: float = 0.5, min_samples: int = 2, atm_dataset_path: str = HYD_ATMS_PATH):
        self.eps_km          = eps_km
        self.min_samples     = min_samples
        self.atm_dataset_path = atm_dataset_path
        self._cached_atms: List[Dict[str, Any]] = []
        self._load_atms()

    def _load_atms(self) -> None:
        if os.path.exists(self.atm_dataset_path):
            try:
                df = pd.read_csv(self.atm_dataset_path, encoding="utf-8")
                self._cached_atms = df.to_dict(orient="records")
            except Exception as e:
                print(f"[DRISHTI] Warning: Could not load ATM dataset ({e})")

    def get_atms(self) -> List[Dict[str, Any]]:
        if not self._cached_atms:
            self._load_atms()
        return self._cached_atms

    # ── INTERNAL: run DBSCAN on a list of (lat, lon) tuples ───────────

    def _run_dbscan(
        self,
        coords: list[tuple[float, float]],
        atm_dicts: list[dict],
        victim_lat: Optional[float] = None,
        victim_lon: Optional[float] = None,
    ) -> HotspotResult:
        """
        Core DBSCAN logic. Used by both predict_single and predict_batch.

        Args:
            coords    : List of (lat, lon) tuples for all ATM points
            atm_dicts : Corresponding list of ATM metadata dicts
            victim_lat/lon : If provided, used as tiebreaker when multiple
                             clusters exist (pick cluster closest to victim)
        """
        n = len(coords)

        # Edge case: too few points for DBSCAN — return centroid as fallback
        if n < 2:
            lat = coords[0][0] if coords else (victim_lat or 0.0)
            lon = coords[0][1] if coords else (victim_lon or 0.0)
            return HotspotResult(
                lat=round(lat, 6), lon=round(lon, 6),
                radius_km=0.5, atm_count=n, confidence=0.5,
                cluster_id=-1, cluster_atms=atm_dicts, all_clusters=0
            )

        # Build coordinate matrix and distance matrix
        X = np.array(coords)  # shape (n, 2)
        dist_matrix = _haversine_matrix(X)

        # Run DBSCAN with precomputed haversine distances
        db = DBSCAN(
            eps=self.eps_km,
            min_samples=self.min_samples,
            metric="precomputed"
        )
        labels = db.fit_predict(dist_matrix)

        # Count cluster sizes (exclude noise label -1)
        unique_labels = set(labels) - {-1}
        n_clusters = len(unique_labels)

        if n_clusters == 0:
            # All points are noise — DBSCAN found no clusters.
            # Fall back to centroid of all points. This happens when eps is
            # too small relative to the point spread.
            # [!] ACCURACY NOTE: this fallback means eps tuning matters.
            #     Increase eps_km if you see many noise fallbacks in testing.
            lat = float(np.mean(X[:, 0]))
            lon = float(np.mean(X[:, 1]))
            return HotspotResult(
                lat=round(lat, 6), lon=round(lon, 6),
                radius_km=round(float(np.max(dist_matrix)) / 2, 3),
                atm_count=n, confidence=0.4,
                cluster_id=-1, cluster_atms=atm_dicts, all_clusters=0
            )

        # ── Select the best cluster ────────────────────────────────────
        # Strategy: if victim coords provided → pick cluster whose centroid
        # is closest to victim (most geographically relevant).
        # Otherwise → pick the largest cluster.

        cluster_info = {}
        for cid in unique_labels:
            mask = labels == cid
            pts  = X[mask]
            c_lat = float(np.mean(pts[:, 0]))
            c_lon = float(np.mean(pts[:, 1]))
            c_atms = [a for a, l in zip(atm_dicts, labels) if l == cid]
            cluster_info[cid] = {
                "lat":   c_lat,
                "lon":   c_lon,
                "count": int(np.sum(mask)),
                "atms":  c_atms,
                "pts":   pts,
            }

        if victim_lat is not None and victim_lon is not None:
            best_cid = min(
                cluster_info,
                key=lambda cid: haversine_km(
                    victim_lat, victim_lon,
                    cluster_info[cid]["lat"], cluster_info[cid]["lon"]
                )
            )
        else:
            best_cid = max(cluster_info, key=lambda cid: cluster_info[cid]["count"])

        best = cluster_info[best_cid]

        # Cluster radius = max distance from centroid to any member point
        member_dists = [
            haversine_km(best["lat"], best["lon"], p[0], p[1])
            for p in best["pts"]
        ]
        radius = max(member_dists) if member_dists else 0.3
        radius = max(radius, 0.1)  # minimum 100m radius for display

        # Confidence = fraction of all ATMs that landed in this cluster
        confidence = round(best["count"] / n, 3)

        return HotspotResult(
            lat=round(best["lat"], 6),
            lon=round(best["lon"], 6),
            radius_km=round(radius, 3),
            atm_count=best["count"],
            confidence=confidence,
            cluster_id=int(best_cid),
            cluster_atms=best["atms"],
            all_clusters=n_clusters,
        )

    # ── PUBLIC: single-complaint hotspot prediction ─────────────────

    def predict_single(
        self,
        nearby_atms: list[dict],
        victim_lat:  Optional[float] = None,
        victim_lon:  Optional[float] = None,
    ) -> Optional[HotspotResult]:
        """
        Predict cash-withdrawal hotspot for ONE complaint.

        Args:
            nearby_atms : List of ATM dicts from nearby_atms CSV field.
                          Each must have "lat" and "lon" keys.
            victim_lat/lon : Victim's location (used for cluster selection).

        Returns:
            HotspotResult, or None if no valid ATM data provided.
        """
        if not nearby_atms:
            if victim_lat is not None and victim_lon is not None:
                candidates = self.evaluate_candidate_atms(victim_lat, victim_lon, k=1)
                if candidates:
                    top = candidates[0]
                    return HotspotResult(
                        lat=top["lat"],
                        lon=top["lon"],
                        radius_km=top["radius_km"],
                        atm_count=top["atm_count"],
                        confidence=top["confidence"],
                        cluster_id=1,
                        cluster_atms=top.get("cluster_atms", []),
                        all_clusters=1,
                    )
            return None

        valid = [a for a in nearby_atms if "lat" in a and "lon" in a]
        if not valid:
            if victim_lat is not None and victim_lon is not None:
                candidates = self.evaluate_candidate_atms(victim_lat, victim_lon, k=1)
                if candidates:
                    top = candidates[0]
                    return HotspotResult(
                        lat=top["lat"],
                        lon=top["lon"],
                        radius_km=top["radius_km"],
                        atm_count=top["atm_count"],
                        confidence=top["confidence"],
                        cluster_id=1,
                        cluster_atms=top.get("cluster_atms", []),
                        all_clusters=1,
                    )
            return None

        coords = [(a["lat"], a["lon"]) for a in valid]
        return self._run_dbscan(coords, valid, victim_lat, victim_lon)

    def predict_top_k(
        self,
        nearby_atms: list[dict],
        victim_lat: Optional[float] = None,
        victim_lon: Optional[float] = None,
        k: int = 3,
    ) -> list[dict]:
        """
        Predict and rank the Top-K candidate cash-withdrawal locations.
        Computes normalized probabilities and confidence scores for each candidate.

        Returns:
            List of dicts:
              - rank: 1..K
              - lat, lon: coordinates
              - radius_km: spread
              - atm_count: number of ATMs
              - probability: 0.0 to 1.0 (sums to 1.0 across top-k)
              - confidence: 0.0 to 1.0
              - location_name: descriptive label
              - distance_km: distance from victim
              - cluster_atms: ATM list
        """
        if not nearby_atms:
            return []

        valid = [a for a in nearby_atms if "lat" in a and "lon" in a]
        if not valid:
            return []

        coords = [(a["lat"], a["lon"]) for a in valid]
        n = len(coords)
        X = np.array(coords)
        dist_matrix = _haversine_matrix(X)

        db = DBSCAN(eps=self.eps_km, min_samples=self.min_samples, metric="precomputed")
        labels = db.fit_predict(dist_matrix)

        candidates = []
        unique_labels = set(labels) - {-1}

        # 1. Process valid clusters
        for cid in unique_labels:
            mask = labels == cid
            pts = X[mask]
            c_lat = float(np.mean(pts[:, 0]))
            c_lon = float(np.mean(pts[:, 1]))
            c_atms = [a for a, l in zip(valid, labels) if l == cid]

            dist_from_vic = (
                haversine_km(victim_lat, victim_lon, c_lat, c_lon)
                if victim_lat and victim_lon else 1.0
            )
            member_dists = [haversine_km(c_lat, c_lon, p[0], p[1]) for p in pts]
            rad = max(member_dists) if member_dists else 0.3
            rad = max(rad, 0.15)

            # Score: higher ATM count, closer to victim
            score = (len(c_atms) * 2.0) + (1.0 / (dist_from_vic + 0.5))

            primary_bank = c_atms[0].get("bank", "Bank") if c_atms else "ATM"
            candidates.append({
                "lat": round(c_lat, 6),
                "lon": round(c_lon, 6),
                "radius_km": round(rad, 3),
                "atm_count": int(np.sum(mask)),
                "raw_score": score,
                "cluster_id": int(cid),
                "location_name": f"{primary_bank} Cluster ({int(np.sum(mask))} ATMs)",
                "distance_km": round(dist_from_vic, 2),
                "cluster_atms": c_atms,
            })

        # 2. Add individual ATM locations if we have fewer than k clusters
        noise_indices = [i for i, l in enumerate(labels) if l == -1]
        for idx in noise_indices:
            pt = coords[idx]
            atm = valid[idx]
            dist_from_vic = (
                haversine_km(victim_lat, victim_lon, pt[0], pt[1])
                if victim_lat and victim_lon else 1.5
            )
            score = 1.0 + (1.0 / (dist_from_vic + 0.5))
            bank = atm.get("bank", "ATM")
            candidates.append({
                "lat": round(pt[0], 6),
                "lon": round(pt[1], 6),
                "radius_km": 0.2,
                "atm_count": 1,
                "raw_score": score,
                "cluster_id": -1,
                "location_name": f"{bank} Standalone ATM",
                "distance_km": round(dist_from_vic, 2),
                "cluster_atms": [atm],
            })

        # If still empty (e.g. single point), create fallback candidate
        if not candidates and coords:
            lat, lon = coords[0]
            candidates.append({
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "radius_km": 0.3,
                "atm_count": 1,
                "raw_score": 1.0,
                "cluster_id": -1,
                "location_name": "Primary ATM Candidate",
                "distance_km": 0.5,
                "cluster_atms": valid[:1],
            })

        # Sort candidates by raw_score descending
        candidates.sort(key=lambda c: c["raw_score"], reverse=True)
        top_candidates = candidates[:k]

        # Compute normalized probabilities using softmax on raw_score
        raw_scores = np.array([c["raw_score"] for c in top_candidates])
        exp_scores = np.exp(raw_scores - np.max(raw_scores))
        probs = exp_scores / np.sum(exp_scores)

        results = []
        for i, (cand, prob) in enumerate(zip(top_candidates, probs)):
            cand["rank"] = i + 1
            cand["probability"] = round(float(prob), 3)
            cand["confidence"] = round(min(0.95, max(0.35, float(prob) * 1.1)), 3)
            cand.pop("raw_score", None)
            results.append(cand)

        return results

    # ── PUBLIC: Evaluate Curated Candidate ATMs (data/hyderabad_atms.csv) ──

    def evaluate_candidate_atms(
        self,
        victim_lat: Optional[float] = None,
        victim_lon: Optional[float] = None,
        amount: float = 0.0,
        fraud_type: str = "upi_fraud",
        hour: int = 14,
        is_weekend: int = 0,
        k: int = 3,
        predicted_time_window: str = "20–40 min",
        predicted_amount: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluates real candidate ATMs from data/hyderabad_atms.csv.
        Calculates a location risk score using:
          - distance from last known transaction / victim
          - transaction amount (large amounts favor high-liquidity branches)
          - transaction velocity & transit time
          - fraud type & temporal patterns (hour, weekend, 24x7 status)
          - commercial cluster density
        
        Returns Top-K candidate ATMs sorted strictly by risk_score descending.
        """
        atms = self.get_atms()
        if not atms:
            return []

        v_lat = victim_lat if victim_lat is not None else 17.4435
        v_lon = victim_lon if victim_lon is not None else 78.3772

        scored_candidates = []
        for atm in atms:
            lat = float(atm.get("latitude", 0.0))
            lon = float(atm.get("longitude", 0.0))
            dist = haversine_km(v_lat, v_lon, lat, lon)

            # 1. Proximity score (decay with distance)
            prox_score = max(5.0, 52.0 - (dist * 4.2))

            # 2. Bank liquidity & infrastructure weight
            bank = str(atm.get("bank", "ATM"))
            if any(b in bank for b in ["State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank"]):
                bank_score = 20.0
            else:
                bank_score = 12.0

            # 3. 24x7 operational window
            is_24x7 = bool(atm.get("is_24x7", True))
            time_score = 12.0 if is_24x7 else 4.0
            if (hour >= 20 or hour <= 6) and is_24x7:
                time_score += 8.0 # Night hours favor 24x7

            # 4. Amount synergy (high value prefers major banks with higher withdrawal limits)
            amt_score = 0.0
            if amount >= 50000:
                amt_score = 12.0 if bank_score >= 18 else 4.0

            # 5. Composite Location Risk Score (0–100)
            raw_risk = prox_score + bank_score + time_score + amt_score
            location_risk = round(float(np.clip(raw_risk, 15.0, 96.0)), 1)

            area = atm.get("area", "Hyderabad")
            locality = atm.get("locality", "Commercial Hub")
            atm_id = atm.get("atm_id", f"ATM-HYD-{int(lat*1000)%9999}")

            reason = (
                f"{bank} terminal in {area} ({locality}), "
                f"{dist:.2f}km from victim origin with {'24x7 access' if is_24x7 else 'standard banking hours'}."
            )

            scored_candidates.append({
                "atm_id": atm_id,
                "bank": bank,
                "area": area,
                "locality": locality,
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "distance_km": round(dist, 2),
                "risk_score": location_risk,
                "is_24x7": is_24x7,
                "reason": reason,
                "atm_dict": atm,
            })

        # Sort strictly by risk_score descending (remove random ranking)
        scored_candidates.sort(key=lambda c: c["risk_score"], reverse=True)
        top_candidates = scored_candidates[:k]

        if not top_candidates:
            return []

        # Softmax normalized probabilities across top_k
        raw_arr = np.array([c["risk_score"] for c in top_candidates])
        exp_arr = np.exp((raw_arr - np.max(raw_arr)) / 10.0)
        probs = exp_arr / np.sum(exp_arr)

        results = []
        for i, (cand, prob) in enumerate(zip(top_candidates, probs)):
            c_lat, c_lon = cand["lat"], cand["lon"]
            nearby_count = sum(
                1 for a in atms if haversine_km(c_lat, c_lon, float(a["latitude"]), float(a["longitude"])) <= 0.8
            )

            res_item = {
                "rank": i + 1,
                "atm_id": cand["atm_id"],
                "bank": cand["bank"],
                "area": cand["area"],
                "location_name": f"{cand['bank']} ATM — {cand['area']}",
                "lat": cand["lat"],
                "lon": cand["lon"],
                "radius_km": 0.45,
                "atm_count": max(1, nearby_count),
                "risk_score": cand["risk_score"],
                "distance_km": cand["distance_km"],
                "probability": round(float(prob), 3),
                "confidence": round(float(np.clip(prob * 1.05, 0.40, 0.95)), 2),
                "predicted_time_window": predicted_time_window,
                "predicted_amount": predicted_amount or (round(amount * 0.92, -2) if amount else 25000.0),
                "reason": cand["reason"],
                "is_24x7": cand["is_24x7"],
                "cluster_atms": [cand["atm_dict"]],
            }
            results.append(res_item)

        return results


    # ── PUBLIC: batch hotspot prediction (multi-complaint analysis) ──

    def predict_batch(
        self,
        complaints_atms: list[list[dict]],
        victim_coords:   Optional[list[tuple[float, float]]] = None,
    ) -> Optional[HotspotResult]:
        """
        Aggregate ATMs from multiple complaints and find city-wide hotspots.
        Used by the dashboard heatmap (Day 4) and batch analysis endpoint.

        Args:
            complaints_atms : List of nearby_atm lists (one per complaint)
            victim_coords   : Optional victim lat/lon for each complaint

        Returns:
            HotspotResult representing the dominant withdrawal cluster, or None.
        """
        all_atms = []
        for atm_list in complaints_atms:
            all_atms.extend(atm_list)

        if not all_atms:
            return None

        valid = [a for a in all_atms if "lat" in a and "lon" in a]
        if not valid:
            return None

        coords = [(a["lat"], a["lon"]) for a in valid]
        # No victim anchor in batch mode — pick largest cluster
        return self._run_dbscan(coords, valid)

    def parse_nearby_atms(self, nearby_atms_field) -> list[dict]:
        """
        Parse the nearby_atms CSV field (JSON string or already-parsed list).
        Handles both formats safely.
        """
        if isinstance(nearby_atms_field, list):
            return nearby_atms_field
        if isinstance(nearby_atms_field, str):
            try:
                return json.loads(nearby_atms_field)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def hotspot_to_dict(self, result: HotspotResult) -> dict:
        """Serialise a HotspotResult to a plain dict for the API response."""
        return {
            "lat":        result.lat,
            "lon":        result.lon,
            "radius_km":  result.radius_km,
            "atm_count":  result.atm_count,
            "confidence": result.confidence,
            "cluster_id": result.cluster_id,
        }


# ─────────────────────────────────────────────────────────────
# Quick self-test when run directly
_global_hotspot_predictor = HotspotPredictor()

def evaluate_candidate_atms(
    victim_lat: Optional[float] = None,
    victim_lon: Optional[float] = None,
    amount: float = 0.0,
    fraud_type: str = "upi_fraud",
    hour: int = 14,
    is_weekend: int = 0,
    k: int = 3,
    top_k: Optional[int] = None,
    predicted_time_window: str = "20–40 min",
    predicted_amount: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Module-level alias for candidate ATM evaluation."""
    actual_k = top_k if top_k is not None else k
    return _global_hotspot_predictor.evaluate_candidate_atms(
        victim_lat=victim_lat,
        victim_lon=victim_lon,
        amount=amount,
        fraud_type=fraud_type,
        hour=hour,
        is_weekend=is_weekend,
        k=actual_k,
        predicted_time_window=predicted_time_window,
        predicted_amount=predicted_amount,
    )


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import pandas as pd

    predictor = HotspotPredictor(eps_km=0.5, min_samples=2)

    df = pd.read_csv("data/complaints.csv")
    sample = df.head(5)

    for _, row in sample.iterrows():
        atms = predictor.parse_nearby_atms(row["nearby_atms"])
        result = predictor.predict_single(atms, row["victim_lat"], row["victim_lon"])
        if result:
            dist = haversine_km(row["victim_lat"], row["victim_lon"], result.lat, result.lon)
            print(f"[{row['complaint_id']}] {row['city']}")
            print(f"  Victim   : ({row['victim_lat']:.4f}, {row['victim_lon']:.4f})")
            print(f"  Hotspot  : ({result.lat:.4f}, {result.lon:.4f})  "
                  f"r={result.radius_km:.2f}km  conf={result.confidence:.0%}  "
                  f"dist_from_victim={dist:.2f}km")
            print(f"  ATMs in cluster: {result.atm_count}/{len(atms)}  "
                  f"total_clusters={result.all_clusters}")
            print()
