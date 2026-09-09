"""
backend/domain/transaction.py — Project DRISHTI
================================================
Encapsulates a financial transaction entity, with velocity,
value threshold, and suspicious pattern checks.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any


class Transaction:
    """
    Domain entity representing a single hop or transaction in the financial network.

    Encapsulation:
      - Validates transaction amounts and timestamps.
      - Implements domain rules: is_high_value, is_rapid, is_suspicious, get_transfer_delay.
    """

    def __init__(
        self,
        transaction_id: str,
        source_account: str,
        destination_account: str,
        amount: float,
        timestamp: Optional[datetime] = None,
        transaction_type: str = "UPI",
        fraud_type: Optional[str] = None,
        source_location: Optional[str] = None,
        destination_location: Optional[str] = None,
        hop_number: int = 1,
        commission_amount: float = 0.0,
        minutes_from_start: int = 0,
        is_terminal_cashout: bool = False,
        to_bank: Optional[str] = None,
        to_ifsc: Optional[str] = None,
    ):
        self.transaction_id = transaction_id
        self.source_account = source_account
        self.destination_account = destination_account
        self.amount = float(amount) if amount is not None else 0.0
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.transaction_type = transaction_type
        self.fraud_type = fraud_type
        self.source_location = source_location
        self.destination_location = destination_location
        self.hop_number = int(hop_number)
        self.commission_amount = float(commission_amount) if commission_amount is not None else 0.0
        self.minutes_from_start = int(minutes_from_start)
        self.is_terminal_cashout = bool(is_terminal_cashout)
        self.to_bank = to_bank
        self.to_ifsc = to_ifsc

        self.validate()

    def validate(self) -> None:
        """Validates domain business rules."""
        if not self.transaction_id:
            raise ValueError("Transaction transaction_id cannot be empty.")
        if self.amount < 0:
            raise ValueError("Transaction amount cannot be negative.")
        if self.commission_amount < 0:
            raise ValueError("Commission amount cannot be negative.")

    def is_high_value(self, threshold: float = 50000.0) -> bool:
        """True if transaction amount meets or exceeds high value threshold."""
        return self.amount >= threshold

    def is_rapid(self, previous: Any, threshold_minutes: float = 15.0, max_minutes: Optional[float] = None) -> bool:
        """True if the transaction occurred within threshold_minutes of the previous event or Transaction."""
        limit = max_minutes if max_minutes is not None else threshold_minutes
        delay = self.get_transfer_delay(previous)
        return delay is not None and 0 <= delay <= limit

    def get_transfer_delay(self, previous: Optional[Any]) -> Optional[float]:
        """Calculates elapsed time in minutes from a previous timestamp or Transaction."""
        if previous is None or not self.timestamp:
            return None
        if isinstance(previous, datetime):
            prev_dt = previous
        elif hasattr(previous, "timestamp") and isinstance(previous.timestamp, datetime):
            prev_dt = previous.timestamp
        else:
            return None
        t1 = self.timestamp.timestamp()
        t0 = prev_dt.timestamp()
        return max(0.0, (t1 - t0) / 60.0)

    def is_suspicious(self) -> bool:
        """Domain heuristic detecting laundering indicators."""
        return self.is_high_value() or self.commission_amount > 0 or self.hop_number >= 3

    def to_dict(self) -> Dict[str, Any]:
        """Serializes domain model to dictionary."""
        return {
            "transaction_id": self.transaction_id,
            "source_account": self.source_account,
            "destination_account": self.destination_account,
            "amount": self.amount,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "transaction_type": self.transaction_type,
            "fraud_type": self.fraud_type,
            "source_location": self.source_location,
            "destination_location": self.destination_location,
            "hop_number": self.hop_number,
            "commission_amount": self.commission_amount,
            "minutes_from_start": self.minutes_from_start,
            "is_terminal_cashout": self.is_terminal_cashout,
            "to_bank": self.to_bank,
            "to_ifsc": self.to_ifsc,
            "is_suspicious": self.is_suspicious(),
        }

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.transaction_id!r} "
            f"{self.source_account} -> {self.destination_account} "
            f"amt={self.amount} hop={self.hop_number}>"
        )
