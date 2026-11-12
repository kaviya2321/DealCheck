"""
DealCheck Master Dev Launcher
Starts FastAPI backend on http://127.0.0.1:8000
Starts Vite React frontend on http://127.0.0.1:5173
Monitors health and coordinates graceful shutdown.
"""

import sys
import subprocess
import time
import os
import signal
import urllib.request
import json

def wait_for_url(url, timeout=30, desc="service"):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status in (200, 304):
                    return True
        except Exception:
            time.sleep(0.5)
    return False

def main():
    print("=" * 60)
    print("Starting DealCheck: PayPal AI Hackathon Application")
    print("=" * 60)

    # 1. Launch FastAPI Backend
    backend_cmd = [
        sys.executable, "-m", "uvicorn", "main:app",
        "--app-dir", "backend",
        "--host", "127.0.0.1",
        "--port", "8000"
    ]
    print("[1/2] Launching FastAPI Backend on http://127.0.0.1:8000...")
    backend_proc = subprocess.Popen(backend_cmd)

    # 2. Launch Vite Frontend
    print("[2/2] Launching Vite React Frontend on http://127.0.0.1:5173...")
    shell_flag = os.name == "nt"
    npm_cmd = "npm.cmd" if shell_flag else "npm"
    frontend_cmd = [npm_cmd, "run", "dev", "--prefix", "frontend", "--", "--host", "127.0.0.1", "--port", "5173"]
    frontend_proc = subprocess.Popen(frontend_cmd, shell=shell_flag)

    # Wait for backend health
    print("\nWaiting for services to become healthy...")
    if wait_for_url("http://127.0.0.1:8000/health", timeout=20, desc="Backend"):
        print("  -> Backend is HEALTHY on http://127.0.0.1:8000/health")
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/health") as resp:
                data = json.loads(resp.read().decode())
                print(f"     [Status]: models_loaded={data.get('models_loaded')}, paypal_configured={data.get('paypal_configured')}")
        except Exception:
            pass
    else:
        print("  [!] Warning: Backend health check timed out.")

    if wait_for_url("http://127.0.0.1:5173", timeout=20, desc="Frontend"):
        print("  -> Frontend is READY on http://127.0.0.1:5173")
    else:
        print("  [!] Warning: Frontend check timed out.")

    print("\n" + "=" * 60)
    print("DealCheck is running!")
    print("  Application UI:  http://127.0.0.1:5173")
    print("  FastAPI Docs:    http://127.0.0.1:8000/docs")
    print("  Health API:      http://127.0.0.1:8000/health")
    print("=" * 60)
    print("Press Ctrl+C to stop all servers.\n")

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print("[!] Backend process exited unexpectedly.")
                break
            if frontend_proc.poll() is not None:
                print("[!] Frontend process exited unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\nStopping DealCheck services...")
    finally:
        for proc in [frontend_proc, backend_proc]:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        print("DealCheck stopped cleanly.")

if __name__ == "__main__":
    main()
