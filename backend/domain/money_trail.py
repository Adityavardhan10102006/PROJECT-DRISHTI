"""
backend/domain/money_trail.py — Project DRISHTI
===============================================
Encapsulates a multi-hop money trail using OOP Composition.
Contains and orchestrates a collection of Transaction entities.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
from backend.domain.transaction import Transaction


class MoneyTrail:
    """
    Composite domain model representing an interconnected chain of fund transfers.

    Composition:
      - Contains a sequence of Transaction objects.
      - Calculates graph topologies, fan-in/fan-out patterns, and laundering metrics.
    """

    def __init__(
        self,
        transactions: Optional[List[Transaction]] = None,
        starting_account: Optional[str] = None,
        initial_amount: Optional[float] = None,
        final_cashout_amount: Optional[float] = None,
        trail_duration_minutes: Optional[float] = None,
        graph_metrics: Optional[Dict[str, Any]] = None,
        data_source: str = "synthetic_demo_dataset",
        mule_accounts: Optional[List[Dict[str, Any]]] = None,
    ):
        self._transactions: List[Transaction] = list(transactions or [])
        self.starting_account = starting_account or (
            self._transactions[0].source_account if self._transactions else "ACC-ORIGIN"
        )
        self.initial_amount = float(
            initial_amount
            if initial_amount is not None
            else (self._transactions[0].amount if self._transactions else 0.0)
        )
        self.final_cashout_amount = float(
            final_cashout_amount
            if final_cashout_amount is not None
            else (self._transactions[-1].amount if self._transactions else self.initial_amount)
        )
        self.trail_duration_minutes = float(trail_duration_minutes or 25.0)
        self.graph_metrics = graph_metrics or {}
        self.data_source = data_source
        self.mule_accounts = list(mule_accounts or [])

    @property
    def transactions(self) -> List[Transaction]:
        """Provides read-only access to encapsulated transactions."""
        return list(self._transactions)

    def add_transaction(self, transaction: Transaction) -> None:
        """Appends a new hop transaction to the trail."""
        if not isinstance(transaction, Transaction):
            raise TypeError("Only Transaction instances can be added to MoneyTrail.")
        self._transactions.append(transaction)
        if len(self._transactions) == 1 and not self.starting_account:
            self.starting_account = transaction.source_account
            self.initial_amount = transaction.amount

    def hop_count(self) -> int:
        """Returns number of hops in the money trail."""
        return len(self._transactions)

    def get_total_amount(self) -> float:
        """Sums transaction amounts across all hops."""
        return sum(t.amount for t in self._transactions)

    def total_amount(self) -> float:
        """Alias for get_total_amount."""
        return self.get_total_amount()

    def get_total_commission(self) -> float:
        """Sums mule commission amounts across all hops."""
        return sum(t.commission_amount for t in self._transactions)

    def total_commission(self) -> float:
        """Alias for get_total_commission."""
        return self.get_total_commission()

    def detect_fan_in(self) -> Dict[str, int]:
        """Detects accounts receiving transfers from multiple distinct sources."""
        in_counts: Dict[str, set] = defaultdict(set)
        for t in self._transactions:
            in_counts[t.destination_account].add(t.source_account)
        return {acc: len(sources) for acc, sources in in_counts.items() if len(sources) > 1}

    def detect_fan_out(self) -> Dict[str, int]:
        """Detects accounts dispersing transfers to multiple distinct destinations."""
        out_counts: Dict[str, set] = defaultdict(set)
        for t in self._transactions:
            out_counts[t.source_account].add(t.destination_account)
        return {acc: len(dests) for acc, dests in out_counts.items() if len(dests) > 1}

    def detect_rapid_movement(self, max_gap_minutes: float = 15.0, max_hop_minutes: Optional[float] = None) -> bool:
        """Returns True if any consecutive hops occurred within max_gap_minutes."""
        limit = max_hop_minutes if max_hop_minutes is not None else max_gap_minutes
        for i in range(1, len(self._transactions)):
            prev = self._transactions[i - 1]
            curr = self._transactions[i]
            if curr.is_rapid(prev.timestamp, threshold_minutes=limit):
                return True
        return False

    def detect_layering(self) -> bool:
        """Returns True if trail exhibits deliberate multi-hop syndication (>= 3 hops)."""
        return self.hop_count() >= 3

    def get_graph(self) -> Dict[str, Any]:
        """Returns nodes and edges format ready for NetworkX or frontend visualization."""
        nodes = set()
        edges = []
        for t in self._transactions:
            nodes.add(t.source_account)
            nodes.add(t.destination_account)
            edges.append({
                "source": t.source_account,
                "target": t.destination_account,
                "amount": t.amount,
                "hop": t.hop_number,
                "id": t.transaction_id,
            })
        return {
            "nodes": [{"id": node} for node in sorted(nodes)],
            "edges": edges,
            "hop_count": self.hop_count(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializes composite MoneyTrail to dictionary compatible with backend.models.MoneyTrail."""
        hops_dicts = []
        for t in self._transactions:
            hops_dicts.append({
                "hop_number": t.hop_number,
                "from_account": t.source_account,
                "to_account": t.destination_account,
                "amount": t.amount,
                "timestamp": t.timestamp.isoformat() if t.timestamp else "",
                "transaction_type": t.transaction_type,
                "commission_deducted": t.commission_amount,
            })

        # Distinct mule accounts
        mules = self.mule_accounts
        if not mules:
            mules = []
            seen = set()
            for t in self._transactions:
                if t.destination_account not in seen:
                    seen.add(t.destination_account)
                    mules.append({
                        "account_number": t.destination_account,
                        "ifsc_code": "SBIN0001423",
                        "bank_name": t.source_location or "Cooperative Bank",
                        "risk_score": 0.85 if t.hop_number >= 2 else 0.45,
                        "linked_accounts": [],
                        "transaction_count": 2,
                        "centrality": 0.05,
                        "flag_reason": f"Multi-hop layering node (hop {t.hop_number}). Rapid dispersal.",
                        "is_historical_mule": t.hop_number >= 3,
                    })

        return {
            "starting_account": self.starting_account,
            "hop_count": self.hop_count(),
            "initial_amount": self.initial_amount,
            "final_cashout_amount": self.final_cashout_amount,
            "trail_duration_minutes": self.trail_duration_minutes,
            "hops": hops_dicts,
            "mule_accounts": mules,
            "graph_metrics": self.graph_metrics,
            "data_source": self.data_source,
            "is_layering": self.detect_layering(),
        }

    def __repr__(self) -> str:
        return f"<MoneyTrail hops={self.hop_count()} origin={self.starting_account!r} amt={self.initial_amount}>"
