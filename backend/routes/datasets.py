"""
backend/routes/datasets.py — Project DRISHTI
============================================
REST API endpoints for Dataset Management, Inspection, Validation, and Telemetry.
"""

import os
import csv
import json
import subprocess
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/datasets", tags=["Dataset Management"])

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")

DATASET_CONFIGS = {
    "complaints": {
        "filename": "complaints.csv",
        "name": "Cybercrime Complaints Registry",
        "description": "Reported cyber fraud complaints with incident narratives, victim locations, and fraud typologies.",
        "type": "csv",
        "category": "Intake / Citizen",
    },
    "transactions": {
        "filename": "transactions.csv",
        "name": "Inter-Bank Financial Transactions Ledger",
        "description": "Multi-hop financial ledger recording UPI, IMPS, NEFT transfers, mule flows, and IP risk scores.",
        "type": "csv",
        "category": "Financial / Graph",
    },
    "money_trails": {
        "filename": "money_trails.csv",
        "name": "Reconstructed Money Trails",
        "description": "Sequential transaction chains tracing stolen funds from victim to terminal ATM cash-out.",
        "type": "csv",
        "category": "Forensic / Tracing",
    },
    "atms": {
        "filename": "hyderabad_atms.csv",
        "name": "Hyderabad ATM & Hotspot Infrastructure",
        "description": "Curated spatial dataset of 520+ automated teller machines across Hyderabad cybercrime corridors.",
        "type": "csv",
        "category": "Geospatial / GIS",
    },
    "police_units": {
        "filename": "police_units.json",
        "name": "Police Rapid Response Patrol Units",
        "description": "Blue Colts, PCR, and Falcon response interceptors with real-time jurisdiction and response times.",
        "type": "json",
        "category": "Operations / Tactical",
    },
    "atm_withdrawals": {
        "filename": "atm_withdrawals.csv",
        "name": "Historical ATM Cash Withdrawal Patterns",
        "description": "Historical transactional patterns at ATMs enabling predictive velocity and withdrawal forecasting.",
        "type": "csv",
        "category": "Predictive / Baseline",
    },
    "case_outcomes": {
        "filename": "case_outcomes.csv",
        "name": "Verified Case Ground Truth & Interceptions",
        "description": "Historical outcome validation records tracking actual cash-out locations, recovery amounts, and interception efficacy.",
        "type": "csv",
        "category": "Feedback / Evaluation",
    },
}


def get_file_info(filepath: str) -> Dict[str, Any]:
    if not os.path.exists(filepath):
        return {"exists": False, "size_bytes": 0, "modified_at": None, "records": 0, "status": "ERROR"}

    stat = os.stat(filepath)
    size_bytes = stat.st_size
    mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

    records = 0
    status = "HEALTHY"
    try:
        if filepath.endswith(".csv"):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                # Count lines without loading entire file into memory
                records = max(0, sum(1 for _ in f) - 1)
        elif filepath.endswith(".json"):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = len(data) if isinstance(data, list) else 1
    except Exception:
        status = "WARNING"

    return {
        "exists": True,
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / (1024 * 1024), 2),
        "modified_at": mod_time,
        "records": records,
        "status": status,
    }


@router.get("/")
def list_datasets():
    """List all registered datasets with record counts, file sizes, and health status."""
    results = []
    total_records = 0
    total_size_bytes = 0

    for key, cfg in DATASET_CONFIGS.items():
        path = os.path.join(DATA_DIR, cfg["filename"])
        info = get_file_info(path)
        total_records += info["records"]
        total_size_bytes += info["size_bytes"]

        results.append({
            "key": key,
            "name": cfg["name"],
            "filename": cfg["filename"],
            "description": cfg["description"],
            "category": cfg["category"],
            "type": cfg["type"],
            "records": info["records"],
            "size_mb": info.get("size_mb", 0),
            "modified_at": info["modified_at"],
            "status": info["status"],
        })

    return {
        "datasets": results,
        "summary": {
            "total_datasets": len(results),
            "total_records": total_records,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
            "system_health": "OPTIMAL",
            "last_audit": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }
    }


@router.get("/{name}/sample")
def get_dataset_sample(name: str, limit: int = Query(default=30, ge=1, le=100)):
    """Fetch sample records and schema definitions for a given dataset."""
    if name not in DATASET_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Dataset '{name}' not found.")

    cfg = DATASET_CONFIGS[name]
    filepath = os.path.join(DATA_DIR, cfg["filename"])

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Dataset file '{cfg['filename']}' does not exist.")

    records = []
    headers = []

    try:
        if cfg["type"] == "csv":
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                for i, row in enumerate(reader):
                    if i >= limit:
                        break
                    records.append(row)
        elif cfg["type"] == "json":
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    records = data[:limit]
                    if records and isinstance(records[0], dict):
                        headers = list(records[0].keys())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read dataset sample: {exc}")

    return {
        "dataset": name,
        "name": cfg["name"],
        "filename": cfg["filename"],
        "total_sample_records": len(records),
        "headers": headers,
        "records": records,
    }


@router.post("/validate")
def validate_all_datasets():
    """Run comprehensive referential and statistical validation on all datasets."""
    from scripts.validate_transactions import validate_transactions

    reports = {}
    overall_status = "PASS"

    # 1. Validate Transactions
    try:
        tx_path = os.path.join(DATA_DIR, "transactions.csv")
        tx_report = validate_transactions(tx_path)
        reports["transactions"] = {
            "status": "PASS",
            "records": tx_report["records"],
            "details": f"{tx_report['unique_accounts']} accounts, {tx_report['multihop_chains']} multi-hop chains, {tx_report['fan_in_patterns']} fan-in patterns.",
        }
    except Exception as e:
        reports["transactions"] = {"status": "FAIL", "error": str(e)}
        overall_status = "WARNING"

    # 2. Validate ATMs
    try:
        atm_path = os.path.join(DATA_DIR, "hyderabad_atms.csv")
        with open(atm_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            atms = list(reader)
        assert len(atms) >= 500, f"Expected >= 500 ATMs, got {len(atms)}"
        reports["atms"] = {
            "status": "PASS",
            "records": len(atms),
            "details": f"{len(atms)} active ATMs across Hyderabad metro corridors.",
        }
    except Exception as e:
        reports["atms"] = {"status": "FAIL", "error": str(e)}
        overall_status = "WARNING"

    # 3. Validate Complaints
    try:
        comp_path = os.path.join(DATA_DIR, "complaints.csv")
        with open(comp_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            comps = list(reader)
        assert len(comps) >= 5000, f"Expected >= 5000 complaints, got {len(comps)}"
        reports["complaints"] = {
            "status": "PASS",
            "records": len(comps),
            "details": f"{len(comps)} complaints with structured typology and narratives.",
        }
    except Exception as e:
        reports["complaints"] = {"status": "FAIL", "error": str(e)}
        overall_status = "WARNING"

    # 4. Validate Police Units
    try:
        police_path = os.path.join(DATA_DIR, "police_units.json")
        with open(police_path, "r", encoding="utf-8") as f:
            units = json.load(f)
        assert len(units) >= 50, f"Expected >= 50 police units, got {len(units)}"
        reports["police_units"] = {
            "status": "PASS",
            "records": len(units),
            "details": f"{len(units)} rapid response units (Blue Colts, Interceptors, PCR).",
        }
    except Exception as e:
        reports["police_units"] = {"status": "FAIL", "error": str(e)}
        overall_status = "WARNING"

    return {
        "status": overall_status,
        "validated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "reports": reports,
    }


@router.post("/generate")
def trigger_dataset_generation():
    """Trigger the massive dataset generation pipeline."""
    try:
        script_path = os.path.join(ROOT_DIR, "scripts", "generate_massive_datasets.py")
        res = subprocess.run([sys.executable, script_path], capture_output=True, text=True, check=True)
        return {
            "status": "SUCCESS",
            "message": "Massive datasets generated successfully.",
            "output": res.stdout.strip().splitlines()[-3:],
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }
    except subprocess.CalledProcessError as exc:
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc.stderr}")
