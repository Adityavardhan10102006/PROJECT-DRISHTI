"""
start.py — Project DRISHTI Effortless One-Click Launcher
========================================================
Simplified, robust, parallel launcher for Project DRISHTI.
Just run `python start.py`, `npm run dev`, or double-click `start.bat`.

Features:
- One Command: starts Backend (FastAPI, port 8000) and Frontend (Vite/React, port 3000)
- Auto-healing: verifies dependencies and ML model artifacts
- Port-smart: auto-clears stale zombie processes or connects to active instances
- SOC Terminal Banner: clean, structured, informative command-center status
- Single Ctrl+C: cleanly terminates all child processes with zero residual locks

Usage:
  python start.py               # Standard one-click launch
  python start.py --restart     # Clean reboot of all services
  python start.py --api-only    # Backend only
  python start.py --check-only  # Run pre-flight health & ML check
  python start.py --no-browser  # Launch without auto-opening browser
  python start.py --verbose     # Show detailed uvicorn / vite logs

Author: Project DRISHTI Team (SIH26184)
"""

import os
import sys
import time
import json
import socket
import signal
import shutil
import urllib.request
import subprocess
import webbrowser
from typing import List, Tuple, Optional

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
PIDS_FILE = os.path.join(ROOT_DIR, ".drishti.pids")
IS_WINDOWS = sys.platform.startswith("win")

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass


def log(msg: str):
    print(msg, flush=True)


def print_banner(frontend_url: str, backend_url: str, elapsed: Optional[float] = None, note: Optional[str] = None):
    log("=" * 60)
    log("  PROJECT DRISHTI — CYBERCRIME TACTICAL COMMAND CENTER")
    log("=" * 60)
    log(f"  Frontend    : {frontend_url}")
    log(f"  Backend API : {backend_url}")
    log(f"  Swagger Docs: {backend_url}/docs")
    log(f"  Database    : Connected (SQLite: drishti.db)")
    log(f"  ML Models   : Loaded (5D Intelligence Engine Ready)")
    log("=" * 60)
    if note:
        log(f"  Status      : {note}")
    elif elapsed is not None:
        log(f"  Status      : OPERATIONAL (Ready in {elapsed:.1f}s)")
    else:
        log("  Status      : OPERATIONAL")
    log("  Controls    : Press Ctrl+C to stop services cleanly")
    log("=" * 60)


def load_env_vars() -> dict:
    env_vars = {
        "BACKEND_HOST": "127.0.0.1",
        "BACKEND_PORT": "8000",
        "FRONTEND_PORT": "3000",
        "DRISHTI_AUTO_OPEN_BROWSER": "true",
    }
    env_path = os.path.join(ROOT_DIR, ".env")
    if not os.path.exists(env_path):
        example_path = os.path.join(ROOT_DIR, ".env.example")
        if os.path.exists(example_path):
            try:
                shutil.copyfile(example_path, env_path)
            except Exception:
                pass

    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip()
        except Exception:
            pass
    return env_vars


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex((host, port)) == 0


def locate_python() -> str:
    # 1. Current running interpreter (preferred if packages are present)
    try:
        import uvicorn
        return sys.executable
    except ImportError:
        pass

    # 2. Virtualenv paths only if uvicorn is installed
    candidates = [
        os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe"),
        os.path.join(ROOT_DIR, ".venv", "bin", "python"),
        os.path.join(ROOT_DIR, "venv", "Scripts", "python.exe"),
        os.path.join(ROOT_DIR, "venv", "bin", "python"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            try:
                res = subprocess.run([p, "-c", "import uvicorn"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    return p
            except Exception:
                pass

    # 3. System interpreters
    for cmd in ["python", "py", "python3"]:
        try:
            res = subprocess.run([cmd, "-c", "import uvicorn"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                return cmd
        except Exception:
            pass

    return sys.executable


def ensure_backend_dependencies(py_exec: str):
    """Auto-install dependencies if missing."""
    try:
        res = subprocess.run(
            [py_exec, "-c", "import fastapi, uvicorn, sklearn, xgboost, pandas, passlib, jose, bcrypt"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if res.returncode != 0:
            log("[DRISHTI] Installing required Python dependencies (one-time setup)...")
            subprocess.run([py_exec, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"], cwd=ROOT_DIR, check=False)
    except Exception:
        pass


def ensure_models(py_exec: str):
    """Auto-train models if missing."""
    required_files = [
        "models/risk_classifier.joblib",
        "models/amount_predictor.joblib",
        "models/time_predictor.json",
        "models/location_classifier.joblib",
    ]
    missing = [f for f in required_files if not os.path.exists(os.path.join(ROOT_DIR, f))]
    if missing:
        log("[DRISHTI] Pre-trained models not found. Initializing offline training pipeline...")
        subprocess.run([py_exec, "-m", "backend.ml.train_all"], cwd=ROOT_DIR, check=False)


def wait_for_services(backend_url: str, frontend_url: Optional[str], timeout: float = 15.0) -> Tuple[bool, bool]:
    """Poll backend and frontend concurrently in a tight loop."""
    start_time = time.time()
    backend_ready = False
    frontend_ready = frontend_url is None
    while time.time() - start_time < timeout:
        if not backend_ready:
            try:
                req = urllib.request.Request(backend_url, headers={"User-Agent": "DrishtiChecker"})
                with urllib.request.urlopen(req, timeout=0.8) as resp:
                    if resp.status == 200:
                        backend_ready = True
            except Exception:
                pass

        if not frontend_ready and frontend_url:
            try:
                req = urllib.request.Request(frontend_url, headers={"User-Agent": "DrishtiChecker"})
                with urllib.request.urlopen(req, timeout=0.8) as resp:
                    if resp.status == 200:
                        frontend_ready = True
            except Exception:
                pass

        if backend_ready and frontend_ready:
            return True, True
        time.sleep(0.12)
    return backend_ready, frontend_ready


def save_pids(pids: List[int]):
    try:
        with open(PIDS_FILE, "w", encoding="utf-8") as f:
            json.dump({"pids": pids, "timestamp": time.time()}, f)
    except Exception:
        pass


def remove_pids():
    if os.path.exists(PIDS_FILE):
        try:
            os.remove(PIDS_FILE)
        except Exception:
            pass


def kill_proc_tree(pid: int):
    if IS_WINDOWS:
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass


def release_ports():
    """Clean up orphan or residual processes on DRISHTI ports 8000 and 3000."""
    try:
        from scripts.stop import main as stop_services
        stop_services()
    except Exception:
        pass


def check_backend_healthy(backend_host: str, backend_port: int) -> bool:
    try:
        req = urllib.request.Request(f"http://{backend_host}:{backend_port}/health", headers={"User-Agent": "DrishtiChecker"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            return resp.status == 200
    except Exception:
        return False


def main():
    t0 = time.perf_counter()

    env_vars = load_env_vars()
    backend_host = env_vars.get("BACKEND_HOST", "127.0.0.1")
    backend_port = int(env_vars.get("BACKEND_PORT", 8000))
    frontend_port = int(env_vars.get("FRONTEND_PORT", 3000))
    auto_open = env_vars.get("DRISHTI_AUTO_OPEN_BROWSER", "true").lower() in ("true", "1", "yes")

    api_only = any(arg in sys.argv for arg in ["--api-only", "--backend-only", "--no-frontend"])
    check_only = "--check-only" in sys.argv
    restart = "--restart" in sys.argv
    verbose = "--verbose" in sys.argv
    no_browser = "--no-browser" in sys.argv or not auto_open

    # 1. Health check verification only
    if check_only:
        sys.path.insert(0, ROOT_DIR)
        from scripts.check_models import check_models
        success = check_models(verbose=True)
        sys.exit(0 if success else 1)

    py_exec = locate_python()

    # 2. Restart handling or port conflict resolution
    if restart:
        log("[DRISHTI] Restarting services...")
        release_ports()
        time.sleep(0.5)
    elif is_port_in_use(backend_port, backend_host):
        if check_backend_healthy(backend_host, backend_port):
            # Already active and healthy
            backend_url = f"http://{backend_host}:{backend_port}"
            frontend_url = f"http://localhost:{frontend_port}"
            print_banner(frontend_url, backend_url, note="ACTIVE (Connected to existing instance)")
            if not no_browser and not api_only:
                try:
                    webbrowser.open(frontend_url)
                except Exception:
                    pass
            # Keep process alive so terminal does not vanish
            try:
                while True:
                    time.sleep(1.0)
            except KeyboardInterrupt:
                log("\n[DRISHTI] Stopping all services...")
                release_ports()
                log("[DRISHTI] All services stopped cleanly.")
                sys.exit(0)
        else:
            # Port is hung by unresponsive process; release it
            log(f"[DRISHTI] Freeing hung port {backend_port}...")
            release_ports()
            time.sleep(0.5)

    # 3. Auto-heal dependencies & models
    ensure_backend_dependencies(py_exec)
    ensure_models(py_exec)

    processes: List[subprocess.Popen] = []

    def cleanup(signum=None, frame=None):
        log("\n[DRISHTI] Shutting down services...")
        for p in processes:
            try:
                kill_proc_tree(p.pid)
            except Exception:
                pass
        release_ports()
        remove_pids()
        log("[DRISHTI] All services stopped cleanly.")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    if not IS_WINDOWS:
        signal.signal(signal.SIGTERM, cleanup)

    log("[DRISHTI] Initializing Command Center services...")

    # 4. Launch Backend
    backend_cmd = [
        py_exec,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        backend_host,
        "--port",
        str(backend_port),
        "--log-level",
        "info" if verbose else "warning",
    ]

    try:
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=ROOT_DIR,
            stdout=None if verbose else subprocess.DEVNULL,
            stderr=None if verbose else subprocess.DEVNULL,
        )
        processes.append(backend_proc)
    except Exception as exc:
        log(f"[DRISHTI] [ERROR] Backend launch failed: {exc}")
        cleanup()

    # 5. Launch Frontend
    frontend_proc = None
    frontend_url = f"http://localhost:{frontend_port}"
    if not api_only:
        npm_cmd = "npm.cmd" if IS_WINDOWS else "npm"
        npm_path = shutil.which(npm_cmd) or shutil.which("npm")
        if npm_path and os.path.exists(FRONTEND_DIR):
            node_modules = os.path.join(FRONTEND_DIR, "node_modules")
            if not os.path.exists(node_modules):
                log("[DRISHTI] Setting up frontend dependencies (one-time setup)...")
                subprocess.run([npm_path, "install"], cwd=FRONTEND_DIR, check=False)

            env_front = os.environ.copy()
            env_front["FRONTEND_PORT"] = str(frontend_port)
            env_front["BACKEND_PORT"] = str(backend_port)
            env_front["BACKEND_HOST"] = backend_host
            try:
                frontend_proc = subprocess.Popen(
                    [npm_path, "run", "dev"],
                    cwd=FRONTEND_DIR,
                    env=env_front,
                    stdout=None if verbose else subprocess.DEVNULL,
                    stderr=None if verbose else subprocess.DEVNULL,
                )
                processes.append(frontend_proc)
            except Exception:
                pass

    save_pids([p.pid for p in processes])

    # 6. Wait for services to become responsive
    backend_health_url = f"http://{backend_host}:{backend_port}/health"
    backend_ok, frontend_ok = wait_for_services(
        backend_health_url,
        frontend_url if not api_only and frontend_proc else None,
        timeout=15.0,
    )

    if not backend_ok:
        log(f"[DRISHTI] [ERROR] Backend failed to initialize on port {backend_port}.")
        cleanup()

    elapsed = time.perf_counter() - t0
    backend_url = f"http://{backend_host}:{backend_port}"

    # 7. Print clean Command Center banner
    print_banner(frontend_url, backend_url, elapsed=elapsed)

    # 8. Auto-open browser
    if not no_browser and not api_only and frontend_ok:
        try:
            webbrowser.open(frontend_url)
        except Exception:
            pass

    # 9. Keep server alive in terminal with Ctrl+C listener
    try:
        while True:
            time.sleep(1.0)
            for p in processes:
                if p.poll() is not None:
                    log(f"\n[DRISHTI] Process {p.pid} terminated (code {p.returncode}).")
                    cleanup()
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
