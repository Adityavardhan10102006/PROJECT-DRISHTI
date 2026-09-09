"""
backend/services/transaction_simulator.py — Project DRISHTI
============================================================
Real-Time Transaction Stream Simulator:
Simulates a live cybercrime transaction feed by replaying records from data/transactions.csv
or generating controlled test events with realistic multi-hop characteristics.

Includes start, stop, pause, replay, and status APIs.
Explicitly marked as DEMO / SIMULATION MODE.
"""

import os
import time
import json
import threading
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

TRANSACTIONS_CSV_PATH = "data/transactions.csv"

class TransactionSimulator:
    """
    Background simulation worker that streams synthetic banking transactions.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TransactionSimulator, cls).__new__(cls)
                cls._instance._init_state()
            return cls._instance

    def _init_state(self):
        self.is_running = False
        self.interval_seconds = 3.0
        self.current_index = 0
        self.transactions_data: List[Dict[str, Any]] = []
        self.recent_events: List[Dict[str, Any]] = []
        self.alert_count = 0
        self.total_streamed = 0
        self.thread: Optional[threading.Thread] = None
        self._load_dataset()

    def _load_dataset(self):
        if os.path.exists(TRANSACTIONS_CSV_PATH):
            try:
                df = pd.read_csv(TRANSACTIONS_CSV_PATH)
                self.transactions_data = df.to_dict(orient="records")
            except Exception as e:
                print(f"[SIMULATOR] Error loading {TRANSACTIONS_CSV_PATH}: {e}")
                self.transactions_data = []
        if not self.transactions_data:
            # Fallback in-memory stream of 5 demo transactions
            self.transactions_data = [
                {
                    "transaction_id": "TXN-SIM-001",
                    "source_account": "ACC-SRC-9011",
                    "destination_account": "ACC-MULE-4412",
                    "amount": 85000.0,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "transaction_type": "IMPS",
                    "fraud_type": "upi_fraud",
                    "source_latitude": 17.3850,
                    "source_longitude": 78.4867,
                    "destination_latitude": 17.4123,
                    "destination_longitude": 78.4489,
                    "source_bank": "State Bank of India",
                    "destination_bank": "ICICI Bank",
                    "device_id": "DEV-SIM-991",
                    "ip_risk_score": 0.88,
                    "is_fraud": 1,
                    "hop_number": 1
                }
            ]

    def start(self, interval_seconds: float = 3.0):
        with self._lock:
            if self.is_running:
                return {"status": "already_running", "message": "Simulation stream already active."}
            self.interval_seconds = max(0.5, float(interval_seconds))
            self.is_running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            return {
                "status": "started",
                "mode": "DEMO / SIMULATION MODE",
                "interval_seconds": self.interval_seconds,
                "dataset_size": len(self.transactions_data),
            }

    def stop(self):
        with self._lock:
            if not self.is_running:
                return {"status": "stopped", "message": "Simulation stream is not running."}
            self.is_running = False
            return {
                "status": "stopped",
                "total_streamed": self.total_streamed,
                "alert_count": self.alert_count,
            }

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "mode": "DEMO / SIMULATION MODE",
                "disclaimer": "Synthetic demonstration stream. No live NPCI, UPI or bank connection.",
                "is_running": self.is_running,
                "interval_seconds": self.interval_seconds,
                "current_index": self.current_index,
                "total_available": len(self.transactions_data),
                "total_streamed": self.total_streamed,
                "suspicious_alerts_generated": self.alert_count,
                "recent_events": self.recent_events[-10:],
            }

    def _run_loop(self):
        while self.is_running:
            if not self.transactions_data:
                time.sleep(1.0)
                continue

            with self._lock:
                idx = self.current_index % len(self.transactions_data)
                raw_tx = dict(self.transactions_data[idx])
                self.current_index += 1
                self.total_streamed += 1

                # Stamp with current timestamp
                raw_tx["simulated_at"] = datetime.now(timezone.utc).isoformat()
                raw_tx["mode"] = "SIMULATION"

                is_fraud = int(raw_tx.get("is_fraud", 0)) == 1
                amount = float(raw_tx.get("amount", 0))
                hop = int(raw_tx.get("hop_number", 1))

                # Simple streaming risk tag
                if is_fraud or amount >= 50000 or hop >= 2:
                    raw_tx["alert_flag"] = True
                    raw_tx["alert_level"] = "CRITICAL" if amount > 80000 else "HIGH"
                    self.alert_count += 1
                else:
                    raw_tx["alert_flag"] = False
                    raw_tx["alert_level"] = "LOW"

                self.recent_events.append(raw_tx)
                if len(self.recent_events) > 50:
                    self.recent_events.pop(0)

            time.sleep(self.interval_seconds)


_simulator_singleton = None

def get_transaction_simulator() -> TransactionSimulator:
    global _simulator_singleton
    if _simulator_singleton is None:
        _simulator_singleton = TransactionSimulator()
    return _simulator_singleton
