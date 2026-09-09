"""
backend/domain/complaint.py — Project DRISHTI
==============================================
Encapsulates a cybercrime complaint entity with input validation,
financial categorization, and geographic coordinates helpers.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple


class Complaint:
    """
    Domain model representing an incoming cybercrime complaint.

    Encapsulation:
      - Validates coordinates and amounts on initialization or explicit validate() call.
      - Provides domain helper methods (is_high_value, get_location, to_dict).
    """

    def __init__(
        self,
        case_id: str,
        fraud_type: str = "upi_fraud",
        amount: float = 0.0,
        timestamp: Optional[datetime] = None,
        victim_lat: Optional[float] = None,
        victim_lon: Optional[float] = None,
        complaint_text: str = "",
        bank_account: Optional[str] = None,
        transaction_id: Optional[str] = None,
        ifsc_code: Optional[str] = None,
        city: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ):
        self.case_id = str(case_id)
        self.fraud_type = str(fraud_type).lower() if fraud_type else "upi_fraud"
        self.amount = float(amount) if amount is not None else 0.0
        self.timestamp = timestamp or datetime.now(timezone.utc)
        effective_lat = victim_lat if victim_lat is not None else latitude
        effective_lon = victim_lon if victim_lon is not None else longitude
        self.victim_lat = float(effective_lat) if effective_lat is not None else None
        self.victim_lon = float(effective_lon) if effective_lon is not None else None
        self.complaint_text = complaint_text or ""
        self.bank_account = bank_account
        self.transaction_id = transaction_id
        self.ifsc_code = ifsc_code
        self.city = city

        self.validate()

    def validate(self) -> None:
        """Enforces domain constraints on complaint fields."""
        if not self.case_id:
            raise ValueError("Complaint case_id cannot be empty.")
        if self.amount < 0:
            raise ValueError("Complaint amount cannot be negative.")
        if self.victim_lat is not None and not (-90.0 <= self.victim_lat <= 90.0):
            raise ValueError(f"Invalid victim_lat: {self.victim_lat}. Latitude must be between -90 and 90.")
        if self.victim_lon is not None and not (-180.0 <= self.victim_lon <= 180.0):
            raise ValueError(f"Invalid victim_lon: {self.victim_lon}. Longitude must be between -180 and 180.")

    def is_high_value(self, threshold: float = 50000.0) -> bool:
        """Determines if the loss exceeds standard priority threshold."""
        return self.amount >= threshold

    def has_location(self) -> bool:
        """Returns whether valid victim coordinates are provided."""
        return self.victim_lat is not None and self.victim_lon is not None

    def has_coordinates(self) -> bool:
        """Alias for has_location."""
        return self.has_location()

    def get_location(self) -> Optional[Tuple[float, float]]:
        """Returns (lat, lon) coordinates tuple if present, else None."""
        if self.has_location():
            return (self.victim_lat, self.victim_lon)
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes domain model to standard dictionary."""
        return {
            "case_id": self.case_id,
            "complaint_text": self.complaint_text,
            "fraud_type": self.fraud_type,
            "amount": self.amount,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "victim_lat": self.victim_lat,
            "victim_lon": self.victim_lon,
            "bank_account": self.bank_account,
            "transaction_id": self.transaction_id,
            "ifsc_code": self.ifsc_code,
            "city": self.city,
            "is_high_value": self.is_high_value(),
        }

    def __repr__(self) -> str:
        return f"<Complaint id={self.case_id!r} type={self.fraud_type!r} amount={self.amount}>"
