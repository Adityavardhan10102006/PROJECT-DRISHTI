"""
backend/repositories/transaction_repository.py — Project DRISHTI
=================================================================
Repository layer for transaction data access.
Decouples business logic from physical storage (CSV / Database).
"""

import os
import csv
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from backend.domain.transaction import Transaction
from backend.domain.money_trail import MoneyTrail

DEFAULT_TXN_CSV = "data/transactions.csv"


class TransactionDataSource(ABC):
    """Abstract Strategy/Interface for transaction storage backends."""

    @abstractmethod
    def get_all(self) -> List[Transaction]:
        """Returns all available transactions."""
        pass

    @abstractmethod
    def find_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Finds a single transaction by ID."""
        pass

    @abstractmethod
    def find_by_account(self, account_number: str) -> List[Transaction]:
        """Finds all transactions involving account_number (source or destination)."""
        pass


class CSVTransactionDataSource(TransactionDataSource):
    """
    High-performance CSV implementation with in-memory indices.
    Loads data once and indexes by ID and Account for sub-millisecond retrieval.
    """

    def __init__(self, csv_path: str = DEFAULT_TXN_CSV):
        self.csv_path = csv_path
        self._loaded: bool = False
        self._transactions: List[Transaction] = []
        self._by_id: Dict[str, Transaction] = {}
        self._by_account: Dict[str, List[Transaction]] = {}

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        if not os.path.exists(self.csv_path):
            self._loaded = True
            return

        txns: List[Transaction] = []
        by_id: Dict[str, Transaction] = {}
        by_acc: Dict[str, List[Transaction]] = {}

        try:
            with open(self.csv_path, mode="r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Parse timestamp safely
                    ts_str = row.get("timestamp", "")
                    ts = None
                    if ts_str:
                        try:
                            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        except Exception:
                            ts = None

                    amt = float(row.get("amount", 0.0) or 0.0)
                    comm = float(row.get("commission_deducted", 0.0) or 0.0)
                    hop = int(row.get("hop_number", 1) or 1)

                    txn = Transaction(
                        transaction_id=row.get("transaction_id", f"TXN-{len(txns)+1}"),
                        source_account=row.get("from_account", row.get("source_account", "ACC-SRC")),
                        destination_account=row.get("to_account", row.get("destination_account", "ACC-DEST")),
                        amount=amt,
                        timestamp=ts or datetime.now(timezone.utc),
                        transaction_type=row.get("transaction_type", "UPI"),
                        fraud_type=row.get("fraud_type"),
                        hop_number=hop,
                        commission_amount=comm,
                    )
                    txns.append(txn)
                    by_id[txn.transaction_id] = txn

                    by_acc.setdefault(txn.source_account, []).append(txn)
                    by_acc.setdefault(txn.destination_account, []).append(txn)

            self._transactions = txns
            self._by_id = by_id
            self._by_account = by_acc
        except Exception as exc:
            print(f"[DRISHTI-REPO] Error loading transactions from {self.csv_path}: {exc}")

        self._loaded = True

    def get_all(self) -> List[Transaction]:
        self._ensure_loaded()
        return list(self._transactions)

    def find_by_id(self, transaction_id: str) -> Optional[Transaction]:
        self._ensure_loaded()
        return self._by_id.get(transaction_id)

    def find_by_account(self, account_number: str) -> List[Transaction]:
        self._ensure_loaded()
        return list(self._by_account.get(account_number, []))


class DatabaseTransactionDataSource(TransactionDataSource):
    """
    SQL Database data source implementation.
    Ready for authorized live banking database connectors.
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        session_factory: Optional[Any] = None,
    ):
        self.connection_string = connection_string
        self.session_factory = session_factory

    def get_all(self) -> List[Transaction]:
        # Production hook for live DB queries
        return []

    def find_by_id(self, transaction_id: str) -> Optional[Transaction]:
        return None

    def find_by_account(self, account_number: str) -> List[Transaction]:
        return []


class TransactionRepository:
    """
    Encapsulates transaction domain data access.
    Exposes clean domain operations to services without leaking file/DB details.
    """

    def __init__(self, data_source: Optional[TransactionDataSource] = None):
        self.data_source = data_source or CSVTransactionDataSource()

    def total_count(self) -> int:
        """Returns total count of available transactions."""
        return len(self.load_transactions())

    def find_all(self, limit: Optional[int] = None) -> List[Transaction]:
        """Returns all or first N transactions."""
        txns = self.load_transactions()
        return txns[:limit] if limit is not None else txns

    def load_transactions(self) -> List[Transaction]:
        """Returns all transactions."""
        return self.data_source.get_all()

    def find_by_transaction_id(self, transaction_id: str) -> Optional[Transaction]:
        """Finds transaction by ID."""
        if not transaction_id:
            return None
        return self.data_source.find_by_id(transaction_id)

    def find_by_account(self, account_number: str) -> List[Transaction]:
        """Finds all transactions associated with an account."""
        if not account_number:
            return []
        return self.data_source.find_by_account(account_number)

    def find_by_source_account(self, account_number: str) -> List[Transaction]:
        """Finds transactions originating from account_number."""
        return self.find_outgoing(account_number)

    def find_outgoing(self, account_number: str) -> List[Transaction]:
        """Finds outbound transactions originating from account_number."""
        all_txns = self.find_by_account(account_number)
        return [t for t in all_txns if t.source_account == account_number]

    def build_money_trail(
        self,
        starting_account: str,
        initial_amount: float,
        max_hops: int = 4,
    ) -> MoneyTrail:
        """
        Assembles a MoneyTrail domain object by traversing sequential hops
        starting from starting_account.
        """
        trail_txns: List[Transaction] = []
        curr_acc = starting_account
        visited = {starting_account}

        for hop_idx in range(1, max_hops + 1):
            outbound = self.find_outgoing(curr_acc)
            # Filter unvisited destination accounts to prevent circular cycles
            candidates = [t for t in outbound if t.destination_account not in visited]
            if not candidates:
                break

            # Pick primary flow (highest amount)
            candidates.sort(key=lambda t: t.amount, reverse=True)
            chosen = candidates[0]
            trail_txns.append(chosen)
            visited.add(chosen.destination_account)
            curr_acc = chosen.destination_account

        return MoneyTrail(
            transactions=trail_txns,
            starting_account=starting_account,
            initial_amount=initial_amount,
            final_cashout_amount=trail_txns[-1].amount if trail_txns else initial_amount,
            data_source="transaction_repository",
        )
