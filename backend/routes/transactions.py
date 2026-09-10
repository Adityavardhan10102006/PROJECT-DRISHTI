"""
backend/routes/transactions.py — Project DRISHTI
================================================
REST API endpoints for Transaction Ledger, Filtering, Search, and Aggregates.
"""

import os
import csv
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix="/transactions", tags=["Financial Transactions"])

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TX_FILE = os.path.join(ROOT_DIR, "data", "transactions.csv")


@router.get("/")
def get_transactions(
    case_id: Optional[str] = Query(default=None, description="Filter by Associated Case ID"),
    account: Optional[str] = Query(default=None, description="Filter by Source or Destination Account"),
    transaction_type: Optional[str] = Query(default=None, description="Filter by Type (UPI, IMPS, ATM_WITHDRAWAL)"),
    is_fraud: Optional[int] = Query(default=None, description="Filter by Fraud flag (1 or 0)"),
    min_amount: Optional[float] = Query(default=None, description="Minimum Transaction Amount"),
    max_amount: Optional[float] = Query(default=None, description="Maximum Transaction Amount"),
    search: Optional[str] = Query(default=None, description="Keyword search"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Query the 22,000+ transaction ledger with multi-parameter filtering and pagination."""
    if not os.path.exists(TX_FILE):
        raise HTTPException(status_code=404, detail="Transactions dataset not found.")

    filtered_records = []
    total_matched = 0

    search_term = search.lower().strip() if search else None
    acct_term = account.strip().upper() if account else None
    case_term = case_id.strip().upper() if case_id else None

    with open(TX_FILE, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filter checks
            if is_fraud is not None and str(row.get("is_fraud")) != str(is_fraud):
                continue

            if transaction_type and row.get("transaction_type", "").upper() != transaction_type.upper():
                continue

            amt = float(row.get("amount", 0))
            if min_amount is not None and amt < min_amount:
                continue
            if max_amount is not None and amt > max_amount:
                continue

            if acct_term:
                if acct_term not in row.get("source_account", "") and acct_term not in row.get("destination_account", ""):
                    continue

            if search_term:
                row_str = " ".join(str(v) for v in row.values()).lower()
                if search_term not in row_str:
                    continue

            total_matched += 1
            if total_matched > offset and len(filtered_records) < limit:
                filtered_records.append(row)

    return {
        "total": total_matched,
        "offset": offset,
        "limit": limit,
        "count": len(filtered_records),
        "transactions": filtered_records,
    }


@router.get("/stats")
def get_transaction_stats():
    """Returns high-level statistics across the entire financial ledger."""
    if not os.path.exists(TX_FILE):
        raise HTTPException(status_code=404, detail="Transactions dataset not found.")

    total_records = 0
    fraud_count = 0
    total_amount = 0.0
    fraud_amount = 0.0
    types_count = {}
    banks_count = {}

    with open(TX_FILE, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_records += 1
            amt = float(row.get("amount", 0))
            total_amount += amt
            is_f = str(row.get("is_fraud")) == "1"
            if is_f:
                fraud_count += 1
                fraud_amount += amt

            ttype = row.get("transaction_type", "OTHER")
            types_count[ttype] = types_count.get(ttype, 0) + 1

            s_bank = row.get("source_bank", "OTHER")
            banks_count[s_bank] = banks_count.get(s_bank, 0) + 1

    return {
        "total_transactions": total_records,
        "fraud_transactions": fraud_count,
        "legitimate_transactions": total_records - fraud_count,
        "fraud_ratio_pct": round((fraud_count / max(1, total_records)) * 100, 2),
        "total_volume_inr": round(total_amount, 2),
        "fraud_volume_inr": round(fraud_amount, 2),
        "average_ticket_inr": round(total_amount / max(1, total_records), 2),
        "types_distribution": types_count,
        "top_banks": sorted(banks_count.items(), key=lambda x: x[1], reverse=True)[:6],
    }
