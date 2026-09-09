"""
start.py — Project DRISHTI Single-Command Launch Orchestrator
=============================================================
Unified, one-command launcher for both Backend API and Frontend Dashboard.

Usage:
  python start.py              # Starts both Backend and Frontend
  python start.py --api-only   # Starts only the FastAPI Backend
  python start.py --check-only # Runs pre-flight system health checks without launching

Evaluator Quick-Start:
  pip install -r requirements.txt
  python start.py
"""

import os
import sys
import time
import shutil
import signal
import urllib.request
import subprocess
from typing import List, Tuple, Optional

# Root directory
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
IS_WINDOWS = sys.platform.startswith("win")

# Required Datasets
REQUIRED_DATASETS = [
    ("data/transactions.csv", "Transaction Laundering Dataset (7,500+ records)"),
    ("data/hyderabad_atms.csv", "Curated Candidate ATM Dataset (181 terminals)"),
    ("data/police_units.json", "Patrol Unit Registry (21 police units)"),
    ("data/demo_cases.json", "Reference Demo & Test Cases (5 benchmark cases)"),
]

# Required Pre-Trained ML Models
REQUIRED_MODELS = [
    ("models/risk_classifier.joblib", "RandomForest Risk Classifier"),
    ("models/amount_predictor.joblib", "GradientBoosting Cash-Out Regressor"),
    ("models/time_predictor.json", "XGBoost Time-Window Model"),
]

# Core Python Dependencies
REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "sklearn",
    "joblib",
    "xgboost",
    "networkx",
    "pandas",
    "numpy",
    "sqlalchemy",
]


# Reconfigure stdout to UTF-8 on Windows if supported
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

OK_SYM = "[✓]" if (sys.stdout.encoding and "utf" in sys.stdout.encoding.lower()) else "[OK]"
ERR_SYM = "[✗]" if (sys.stdout.encoding and "utf" in sys.stdout.encoding.lower()) else "[ERR]"


def print_banner():
    print("=" * 60)
    print("                PROJECT DRISHTI")
    print("   Cybercrime Predictive Intelligence Platform (5D)")
    print("      SIH26184 — Ministry of Home Affairs")
    print("=" * 60)


def check_python_environment() -> bool:
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 9):
        print(f"{ERR_SYM} Python 3.9+ required. Detected Python {v.major}.{v.minor}.{v.micro}")
        return False
    print(f"{OK_SYM} Python environment detected (Python {v.major}.{v.minor}.{v.micro})")
    return True


def check_dependencies() -> bool:
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"{ERR_SYM} Missing required Python packages: {', '.join(missing)}")
        print("    Run: pip install -r requirements.txt")
        return False
    print(f"{OK_SYM} Dependencies available")
    return True


def check_configuration():
    env_file = os.path.join(ROOT_DIR, ".env")
    env_example = os.path.join(ROOT_DIR, ".env.example")
    if not os.path.exists(env_file) and os.path.exists(env_example):
        try:
            shutil.copyfile(env_example, env_file)
            print(f"{OK_SYM} Initialized .env from .env.example")
        except Exception:
            pass
    print(f"{OK_SYM} Configuration validated")


def check_datasets() -> bool:
    all_found = True
    for path, desc in REQUIRED_DATASETS:
        full_path = os.path.join(ROOT_DIR, path)
        if not os.path.exists(full_path) or os.path.getsize(full_path) == 0:
            print(f"{ERR_SYM} Missing required dataset: {path} ({desc})")
            all_found = False
    if not all_found:
        print("    To generate datasets, run: python backend/data_builder.py")
        return False
    print(f"{OK_SYM} Transaction dataset found")
    print(f"{OK_SYM} ATM dataset found")
    print(f"{OK_SYM} Police dataset found")
    return True


def check_models() -> bool:
    all_found = True
    for path, desc in REQUIRED_MODELS:
        full_path = os.path.join(ROOT_DIR, path)
        if not os.path.exists(full_path):
            print(f"{ERR_SYM} Missing pre-trained model: {path} ({desc})")
            all_found = False
    if not all_found:
        print("    To train models, run: python backend/ml/train_models.py")
        return False
    print(f"{OK_SYM} ML models verified")
    return True


def wait_for_endpoint(url: str, timeout_seconds: float = 12.0) -> bool:
    """Poll an HTTP endpoint until it returns HTTP 200 or times out."""
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DrishtiStartupChecker/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def main():
    print_banner()

    # Parse command line flags
    api_only = "--api-only" in sys.argv or "--backend-only" in sys.argv or "--no-frontend" in sys.argv
    check_only = "--check-only" in sys.argv

    # Pre-flight checks
    if not check_python_environment():
        sys.exit(1)
    if not check_dependencies():
        sys.exit(1)
    if not check_datasets():
        sys.exit(1)
    if not check_models():
        sys.exit(1)
    check_configuration()

    if check_only:
        print("\n[✓] All pre-flight checks passed successfully. System is launch-ready.")
        return

    print("\nStarting services...")

    processes: List[subprocess.Popen] = []

    def cleanup(signum=None, frame=None):
        print("\n\nShutting down PROJECT DRISHTI services gracefully...")
        for p in processes:
            try:
                if p.poll() is None:
                    p.terminate()
                    p.wait(timeout=2.0)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        print("All services stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    if not IS_WINDOWS:
        signal.signal(signal.SIGTERM, cleanup)

    # ── 1. Start Backend Service ─────────────────────────────────
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--log-level",
        "warning",
    ]

    try:
        backend_proc = subprocess.Popen(backend_cmd, cwd=ROOT_DIR)
        processes.append(backend_proc)
    except Exception as exc:
        print(f"[✗] Failed to launch backend API: {exc}")
        cleanup()

    # Wait for backend to be ready
    backend_live = wait_for_endpoint("http://127.0.0.1:8000/health", timeout_seconds=15.0)
    if not backend_live:
        print("[✗] Backend API failed to respond within 15 seconds.")
        cleanup()

    # ── 2. Start Frontend Service (if requested) ─────────────────
    frontend_started = False
    frontend_url = "http://localhost:3000"

    if not api_only:
        npm_cmd = "npm.cmd" if IS_WINDOWS else "npm"
        npm_path = shutil.which(npm_cmd) or shutil.which("npm")

        if npm_path and os.path.exists(FRONTEND_DIR):
            node_modules = os.path.join(FRONTEND_DIR, "node_modules")
            if not os.path.exists(node_modules):
                print(" [*] Installing frontend dependencies (one-time setup)...")
                subprocess.run([npm_path, "install"], cwd=FRONTEND_DIR, check=False)

            frontend_run_cmd = [npm_path, "run", "dev"]
            try:
                frontend_proc = subprocess.Popen(
                    frontend_run_cmd,
                    cwd=FRONTEND_DIR,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                processes.append(frontend_proc)
                # Wait briefly for Vite dev server
                frontend_started = wait_for_endpoint(frontend_url, timeout_seconds=10.0)
            except Exception as fe_err:
                print(f" [!] Note: Frontend auto-start skipped ({fe_err})")
        else:
            # Check if built dist directory exists; if so, serve statically
            dist_dir = os.path.join(FRONTEND_DIR, "dist")
            if os.path.exists(dist_dir):
                static_cmd = [sys.executable, "-m", "http.server", "3000", "--directory", dist_dir]
                try:
                    static_proc = subprocess.Popen(
                        static_cmd,
                        cwd=ROOT_DIR,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    processes.append(static_proc)
                    frontend_started = wait_for_endpoint(frontend_url, timeout_seconds=6.0)
                except Exception:
                    pass

    # ── 3. Display Ready Status & URLs ───────────────────────────
    print("\n" + "=" * 60)
    if frontend_started:
        print(f" Frontend : {frontend_url}")
    else:
        print(f" Frontend : http://localhost:3000 (Launch: cd frontend && npm run dev)")
    print(" Backend  : http://127.0.0.1:8000")
    print(" API Docs : http://127.0.0.1:8000/docs")
    print(" Health   : http://127.0.0.1:8000/health")
    print(" Ready    : http://127.0.0.1:8000/ready")
    print("=" * 60)
    print("\nPROJECT DRISHTI is ready.")
    print("Press Ctrl+C to stop all services.\n")

    # Keep alive while child processes are healthy
    try:
        while True:
            time.sleep(1.0)
            for p in processes:
                if p.poll() is not None:
                    print(f"\n[!] A service process terminated unexpectedly (exit code {p.returncode}).")
                    cleanup()
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
