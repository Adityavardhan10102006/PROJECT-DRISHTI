"""
backend/domain/atm.py — Project DRISHTI
========================================
Encapsulates an Automated Teller Machine (ATM) terminal entity,
with Haversine distance calculations and metadata properties.
"""

import math
from typing import Dict, Any, Optional

EARTH_RADIUS_KM = 6371.0


class ATM:
    """
    Domain entity representing an ATM / cash-out terminal.

    Encapsulation:
      - Holds geospatial coordinates and operational metadata.
      - Implements distance_to calculation directly on the entity.
    """

    def __init__(
        self,
        atm_id: str,
        bank: str,
        latitude: float,
        longitude: float,
        area: Optional[str] = None,
        locality: Optional[str] = None,
        city: str = "Hyderabad",
        pincode: Optional[str] = None,
        is_24x7: bool = True,
        accessibility: str = "HIGH",
        historical_mule_hits: int = 0,
        location_name: Optional[str] = None,
        cash_capacity: Optional[str] = None,
    ):
        self.atm_id = str(atm_id)
        self.bank = str(bank)
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.area = area or locality or location_name or "Central Area"
        self.locality = locality or self.area
        self.location_name = location_name or f"{self.bank} — {self.area}"
        self.city = city
        self.pincode = str(pincode) if pincode else None
        self.is_24x7 = bool(is_24x7)
        self.accessibility = str(accessibility).upper()
        self.cash_capacity = cash_capacity or "NORMAL"
        self.historical_mule_hits = int(historical_mule_hits)

        self.validate()

    def is_open_now(self, hour: Optional[int] = None) -> bool:
        """Determines if the ATM is operational at the given hour."""
        if self.is_24x7:
            return True
        h = hour if hour is not None else 12
        return 6 <= h <= 22

    def validate(self) -> None:
        """Validates coordinates and identifier."""
        if not self.atm_id:
            raise ValueError("ATM atm_id cannot be empty.")
        if not (-90.0 <= self.latitude <= 90.0):
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not (-180.0 <= self.longitude <= 180.0):
            raise ValueError(f"Invalid longitude: {self.longitude}")

    def distance_to(self, target_lat: float, target_lon: float) -> float:
        """Calculates Haversine distance in kilometers from this ATM to target coordinates."""
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

    def to_dict(self) -> Dict[str, Any]:
        """Serializes ATM entity to dictionary."""
        return {
            "atm_id": self.atm_id,
            "bank": self.bank,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "area": self.area,
            "locality": self.locality,
            "city": self.city,
            "pincode": self.pincode,
            "is_24x7": self.is_24x7,
            "accessibility": self.accessibility,
            "historical_mule_hits": self.historical_mule_hits,
        }

    def __repr__(self) -> str:
        return f"<ATM id={self.atm_id!r} bank={self.bank!r} lat={self.latitude:.4f} lon={self.longitude:.4f}>"
