"""
start.py — Project DRISHTI Single-Command Cross-Platform Launcher
================================================================
Unified, one-command launcher for both Backend API and Frontend Dashboard.

Usage:
  python start.py               # Starts both Backend and Frontend, auto-opens browser
  python start.py --api-only    # Starts only the FastAPI Backend
  python start.py --check-only  # Runs pre-flight system health checks without launching
  python start.py --no-browser  # Starts services without auto-launching browser

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
from typing import List, Optional

# Root directory
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
PIDS_FILE = os.path.join(ROOT_DIR, ".drishti.pids")
IS_WINDOWS = sys.platform.startswith("win")

# Reconfigure stdout to UTF-8 on Windows if supported
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

OK_SYM = "[OK]"
ERR_SYM = "[ERROR]"
WARN_SYM = "[WARN]"


def load_env_vars() -> dict:
    """Load key variables from .env if present."""
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


def print_banner():
    print("=" * 65)
    print(" [DRISHTI] ===============================================")
    print(" [DRISHTI] PROJECT DRISHTI — Fast One-Click Launcher")
    print(" [DRISHTI] Cybercrime Predictive Intelligence Platform (5D)")
    print(" [DRISHTI] SIH26184 — Ministry of Home Affairs")
    print(" [DRISHTI] ===============================================")
    print("=" * 65)


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check whether a local TCP port is already open/listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def locate_python() -> str:
    """Find the best Python executable (current interpreter or virtualenv)."""
    # 1. First test current running interpreter
    try:
        import uvicorn
        return sys.executable
    except ImportError:
        pass

    # 2. Check virtualenv candidates
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
    return sys.executable


def check_preflight(verbose: bool = True) -> bool:
    """Run all pre-flight sanity checks."""
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 9):
        print(f"{ERR_SYM} Python 3.9+ required. Detected: {v.major}.{v.minor}.{v.micro}")
        return False
    if verbose:
        print(f"{OK_SYM} Python detected ({v.major}.{v.minor}.{v.micro})")

    # Node / npm check
    npm_cmd = "npm.cmd" if IS_WINDOWS else "npm"
    npm_path = shutil.which(npm_cmd) or shutil.which("npm")
    if npm_path:
        if verbose:
            print(f"{OK_SYM} Node.js / npm detected ({npm_path})")
    else:
        if verbose:
            print(f"{WARN_SYM} Node.js/npm not found in PATH. Frontend must be run separately or via static server.")

    # Virtual Environment
    py_exec = locate_python()
    if ".venv" in py_exec or "venv" in py_exec or hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix):
        if verbose:
            print(f"{OK_SYM} Virtual environment active")
    else:
        if verbose:
            print(f"{OK_SYM} Python environment ({py_exec})")

    # Dependencies check
    req_pkgs = ["fastapi", "uvicorn", "joblib", "xgboost", "sklearn", "pandas", "numpy", "networkx"]
    missing_pkgs = []
    for pkg in req_pkgs:
        try:
            __import__(pkg)
        except ImportError:
            missing_pkgs.append(pkg)
    if missing_pkgs:
        print(f"{ERR_SYM} Missing Python packages: {', '.join(missing_pkgs)}")
        print("      Run setup.bat or: pip install -r requirements.txt")
        return False
    if verbose:
        print(f"{OK_SYM} Backend dependencies")

    # Frontend dependencies check
    node_modules = os.path.join(FRONTEND_DIR, "node_modules")
    if os.path.exists(node_modules):
        if verbose:
            print(f"{OK_SYM} Frontend dependencies")
    else:
        if verbose:
            print(f"{WARN_SYM} Frontend node_modules missing. Will install on first run.")

    # Model & Artifact check
    sys.path.insert(0, ROOT_DIR)
    try:
        from scripts.check_models import check_models
        if not check_models(verbose=False):
            print(f"{ERR_SYM} ML models not prepared or corrupted.")
            print("      To train models offline, run: python -m backend.ml.train_all")
            return False
        if verbose:
            print(f"{OK_SYM} ML models (Location, Time, Amount, Risk)")
    except Exception as e:
        print(f"{ERR_SYM} Model check failed: {e}")
        return False

    # Database check
    try:
        from backend.database import init_db
        init_db()
        if verbose:
            print(f"{OK_SYM} Database initialized (data/drishti.db)")
    except Exception as e:
        print(f"{ERR_SYM} Database initialization error: {e}")
        return False

    return True


def wait_for_endpoint(url: str, timeout_seconds: float = 15.0) -> bool:
    """Poll an HTTP endpoint until it returns HTTP 200 or times out."""
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DrishtiStartupChecker/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.25)
    return False


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
    """Terminate a process and its children cleanly."""
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


def main():
    t0_start = time.perf_counter()
    print_banner()

    env_vars = load_env_vars()
    backend_host = env_vars.get("BACKEND_HOST", "127.0.0.1")
    backend_port = int(env_vars.get("BACKEND_PORT", 8000))
    frontend_port = int(env_vars.get("FRONTEND_PORT", 3000))
    auto_open = env_vars.get("DRISHTI_AUTO_OPEN_BROWSER", "true").lower() in ("true", "1", "yes")

    api_only = "--api-only" in sys.argv or "--backend-only" in sys.argv or "--no-frontend" in sys.argv
    check_only = "--check-only" in sys.argv
    no_browser = "--no-browser" in sys.argv or not auto_open

    # Run preflight checks
    if not check_preflight(verbose=True):
        sys.exit(1)

    if check_only:
        print("\n[OK] Pre-flight validation passed. PROJECT DRISHTI is launch-ready.")
        sys.exit(0)

    # Check for port conflicts
    if is_port_in_use(backend_port, backend_host):
        print(f"\n{ERR_SYM} Backend port {backend_port} is already in use.")
        print(f"      To stop existing DRISHTI processes, run: stop.bat")
        print(f"      Or check: http://{backend_host}:{backend_port}\n")
        sys.exit(1)

    if not api_only and is_port_in_use(frontend_port, "localhost"):
        print(f"\n{ERR_SYM} Frontend port {frontend_port} is already in use.")
        print(f"      To stop existing DRISHTI processes, run: stop.bat")
        print(f"      Or check: http://localhost:{frontend_port}\n")
        sys.exit(1)

    py_exec = locate_python()
    processes: List[subprocess.Popen] = []

    def cleanup(signum=None, frame=None):
        print("\n[DRISHTI] Shutting down PROJECT DRISHTI services gracefully...")
        for p in processes:
            try:
                kill_proc_tree(p.pid)
            except Exception:
                pass
        remove_pids()
        print("[DRISHTI] All services stopped cleanly.")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    if not IS_WINDOWS:
        signal.signal(signal.SIGTERM, cleanup)

    # ── 1. Start Backend Service ─────────────────────────────────
    print(f"\n[DRISHTI] Starting backend API on {backend_host}:{backend_port}...")
    t_backend_start = time.perf_counter()
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
        "warning",
    ]

    try:
        backend_proc = subprocess.Popen(backend_cmd, cwd=ROOT_DIR)
        processes.append(backend_proc)
    except Exception as exc:
        print(f"{ERR_SYM} Failed to launch backend: {exc}")
        cleanup()

    # Poll for backend readiness
    backend_live = wait_for_endpoint(f"http://{backend_host}:{backend_port}/health", timeout_seconds=15.0)
    t_backend_ready = time.perf_counter()
    backend_latency = (t_backend_ready - t_backend_start) * 1000

    if not backend_live:
        print(f"{ERR_SYM} Backend API failed to respond within 15 seconds.")
        cleanup()
    print(f"{OK_SYM} Backend ready ({backend_latency:.1f}ms) -> http://{backend_host}:{backend_port}")

    # ── 2. Start Frontend Service (if requested) ─────────────────
    frontend_started = False
    frontend_url = f"http://localhost:{frontend_port}"

    if not api_only:
        npm_cmd = "npm.cmd" if IS_WINDOWS else "npm"
        npm_path = shutil.which(npm_cmd) or shutil.which("npm")

        if npm_path and os.path.exists(FRONTEND_DIR):
            node_modules = os.path.join(FRONTEND_DIR, "node_modules")
            if not os.path.exists(node_modules):
                print("[DRISHTI] Installing frontend dependencies (one-time setup)...")
                subprocess.run([npm_path, "install"], cwd=FRONTEND_DIR, check=False)

            print(f"[DRISHTI] Starting React/Vite dashboard on port {frontend_port}...")
            t_frontend_start = time.perf_counter()
            env_front = os.environ.copy()
            env_front["FRONTEND_PORT"] = str(frontend_port)
            env_front["BACKEND_PORT"] = str(backend_port)
            env_front["BACKEND_HOST"] = backend_host

            frontend_run_cmd = [npm_path, "run", "dev"]
            try:
                frontend_proc = subprocess.Popen(
                    frontend_run_cmd,
                    cwd=FRONTEND_DIR,
                    env=env_front,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                processes.append(frontend_proc)
                frontend_started = wait_for_endpoint(frontend_url, timeout_seconds=12.0)
                t_frontend_ready = time.perf_counter()
                frontend_latency = (t_frontend_ready - t_frontend_start) * 1000
                if frontend_started:
                    print(f"{OK_SYM} Frontend ready ({frontend_latency:.1f}ms) -> {frontend_url}")
                else:
                    print(f"{WARN_SYM} Frontend server started, continuing to monitor...")
            except Exception as fe_err:
                print(f"{WARN_SYM} Frontend auto-start skipped: {fe_err}")

    # Save active PIDs for stop.bat
    save_pids([p.pid for p in processes])

    t_total = time.perf_counter() - t0_start

    # ── 3. Display Ready Status & URLs ───────────────────────────
    print("\n" + "=" * 65)
    print(f" [DRISHTI] Application Ready in {t_total:.2f} seconds!")
    print("=" * 65)
    if frontend_started:
        print(f"  Frontend Dashboard : {frontend_url}")
    else:
        print(f"  Frontend Dashboard : {frontend_url} (or run: cd frontend && npm run dev)")
    print(f"  Backend API        : http://{backend_host}:{backend_port}")
    print(f"  API Documentation  : http://{backend_host}:{backend_port}/docs")
    print(f"  System Health      : http://{backend_host}:{backend_port}/health")
    print("=" * 65)
    print("\n[DRISHTI] Platform is active. Press Ctrl+C or run stop.bat to exit.\n")

    # ── 4. Automatically Open Browser ────────────────────────────
    if not no_browser and frontend_started:
        try:
            print(f"[DRISHTI] Opening {frontend_url} in default browser...")
            webbrowser.open(frontend_url)
        except Exception:
            pass

    # Monitor processes
    try:
        while True:
            time.sleep(1.0)
            for p in processes:
                if p.poll() is not None:
                    print(f"\n[!] A service process terminated unexpectedly (PID {p.pid}, exit code {p.returncode}).")
                    cleanup()
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
