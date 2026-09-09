"""
backend/domain/police_unit.py — Project DRISHTI
================================================
Encapsulates a police patrol unit / station entity with
geographic tracking, transit speed modeling, and ETA estimation.
"""

import math
from typing import Dict, Any, Optional

EARTH_RADIUS_KM = 6371.0


class PoliceUnit:
    """
    Domain entity representing a police patrol unit or station.

    Encapsulation:
      - Holds station, vehicle type, and speed configuration.
      - Computes direct distance and transit ETA to target coordinates.
    """

    def __init__(
        self,
        unit_id: str,
        unit_name: str,
        station_name: str = "Central Police Station",
        latitude: float = 17.4400,
        longitude: float = 78.3800,
        speed_kmh: float = 35.0,
        is_available: bool = True,
        officer_in_charge: Optional[str] = None,
    ):
        self.unit_id = str(unit_id)
        self.unit_name = str(unit_name)
        self.station_name = str(station_name)
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.speed_kmh = max(5.0, float(speed_kmh))
        self.is_available = bool(is_available)
        self.officer_in_charge = officer_in_charge or "Duty Officer"

        self.validate()

    def can_intercept(self, distance_km: float, time_window_minutes: float) -> bool:
        """Determines if the unit can intercept within the given time window."""
        return self.estimate_eta_minutes(distance_km) <= time_window_minutes

    def validate(self) -> None:
        """Validates unit attributes."""
        if not self.unit_id:
            raise ValueError("PoliceUnit unit_id cannot be empty.")
        if not (-90.0 <= self.latitude <= 90.0):
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not (-180.0 <= self.longitude <= 180.0):
            raise ValueError(f"Invalid longitude: {self.longitude}")

    def distance_to(self, target_lat: float, target_lon: float) -> float:
        """Calculates Haversine distance in kilometers to target coordinates."""
        try:
            r = math.radians
            dlat = r(target_lat - self.latitude)
            dlon = r(target_lon - self.longitude)
            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(r(self.latitude)) * math.cos(r(target_lat)) * math.sin(dlon / 2) ** 2
            )
            return float(EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))
        except Exception:
            return 999.0

    def estimate_eta_minutes(
        self,
        target_lat_or_dist: float,
        target_lon: Optional[float] = None,
        city_traffic_factor: float = 1.35,
    ) -> float:
        """Estimates transit ETA in minutes accounting for urban road curvature and traffic."""
        if target_lon is not None:
            dist_km = self.distance_to(target_lat_or_dist, target_lon)
        else:
            dist_km = float(target_lat_or_dist)
        # Effective road travel distance (Manhattan/city curvature adjustment)
        effective_dist = dist_km * city_traffic_factor
        hours = effective_dist / self.speed_kmh
        return float(round(hours * 60.0, 1))

    def to_dict(self) -> Dict[str, Any]:
        """Serializes PoliceUnit entity to dictionary."""
        return {
            "unit_id": self.unit_id,
            "unit_name": self.unit_name,
            "station_name": self.station_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "speed_kmh": self.speed_kmh,
            "is_available": self.is_available,
            "officer_in_charge": self.officer_in_charge,
        }

    def __repr__(self) -> str:
        return f"<PoliceUnit id={self.unit_id!r} name={self.unit_name!r} station={self.station_name!r}>"
