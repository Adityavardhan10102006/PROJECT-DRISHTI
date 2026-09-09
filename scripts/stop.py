"""
scripts/stop.py — Safely Terminate DRISHTI Services
===================================================
Gracefully stops backend and frontend processes tracked in .drishti.pids
or cleans up listeners on DRISHTI ports without killing unrelated Python/Node tasks.
"""

import os
import sys
import json
import socket
import subprocess

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PIDS_FILE = os.path.join(ROOT_DIR, ".drishti.pids")
IS_WINDOWS = sys.platform.startswith("win")


def kill_pid(pid: int):
    if IS_WINDOWS:
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    else:
        try:
            import signal
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass


def find_pids_on_port(port: int) -> list:
    """Find PID listening on a specific local port (Windows netstat)."""
    pids = []
    if IS_WINDOWS:
        try:
            out = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True, text=True, errors="ignore")
            for line in out.strip().splitlines():
                parts = line.split()
                if len(parts) >= 5 and "LISTENING" in parts:
                    pid = int(parts[-1])
                    if pid > 0 and pid not in pids:
                        pids.append(pid)
        except Exception:
            pass
    return pids


def main():
    print("[DRISHTI] Stopping PROJECT DRISHTI services...")
    stopped_any = False

    # 1. Kill tracked PIDs from .drishti.pids
    if os.path.exists(PIDS_FILE):
        try:
            with open(PIDS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            pids = data.get("pids", [])
            for pid in pids:
                print(f" [*] Terminating DRISHTI process (PID {pid})...")
                kill_pid(pid)
                stopped_any = True
            os.remove(PIDS_FILE)
        except Exception as e:
            print(f" [!] Note reading PID file: {e}")

    # 2. Check DRISHTI ports (8000 and 3000) for residual listeners
    for port in [8000, 3000]:
        port_pids = find_pids_on_port(port)
        for p in port_pids:
            print(f" [*] Releasing port {port} (PID {p})...")
            kill_pid(p)
            stopped_any = True

    if stopped_any:
        print("[OK] All PROJECT DRISHTI processes have been stopped.")
    else:
        print("[OK] No active PROJECT DRISHTI processes were found running.")


if __name__ == "__main__":
    main()
