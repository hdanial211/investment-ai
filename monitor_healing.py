# monitor_healing.py
import os
import sys
import time
import socket
import urllib.request
import subprocess
import logging
from datetime import datetime
try:
    import psutil
except ImportError:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(base_dir, "backend", "venv", "Scripts", "python.exe")
    if os.path.exists(venv_python) and sys.executable.lower() != os.path.abspath(venv_python).lower():
        print(f"psutil not found. Re-running script with virtual env python: {venv_python}")
        result = subprocess.run([venv_python] + sys.argv)
        sys.exit(result.returncode)
    else:
        print("Error: psutil is not installed. Please run via the virtual environment or install it manually.")
        sys.exit(1)


# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
BACKEND_URL = "http://localhost:8000/api/state"
FRONTEND_PORT = 5173
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
LOG_FILE = os.path.join(BASE_DIR, "healing.log")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ]
)
logger = logging.getLogger("AutoHealing")

def check_port(port: int) -> bool:
    """Check if a TCP port is open locally on localhost (IPv4/IPv6)."""
    for host in ["localhost", "127.0.0.1", "::1"]:
        try:
            s = socket.create_connection((host, port), timeout=1.5)
            s.close()
            return True
        except Exception:
            pass
    return False

def check_backend_api() -> bool:
    """Test if the backend FastAPI is serving requests successfully."""
    try:
        req = urllib.request.Request(BACKEND_URL, headers={'User-Agent': 'Auto-Healing Monitor'})
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.status == 200:
                return True
    except Exception as e:
        logger.warning(f"Backend API check failed: {e}")
    return False

def kill_backend_processes() -> int:
    """Find and terminate any existing backend processes to prevent port conflicts."""
    logger.info("Terminating existing backend processes...")
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd = proc.info['cmdline']
            if cmd:
                cmd_str = " ".join(cmd).lower()
                # Check for python processes running uvicorn on api:app or running api.py
                if "python" in proc.info['name'].lower() and ("api:app" in cmd_str or "api.py" in cmd_str):
                    logger.info(f"Terminating backend Python process PID {proc.pid}")
                    proc.kill()
                    killed_count += 1
                # Check for cmd windows holding uvicorn
                elif "cmd.exe" in proc.info['name'].lower() and "uvicorn api:app" in cmd_str:
                    logger.info(f"Terminating backend CMD terminal process PID {proc.pid}")
                    proc.kill()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return killed_count

def kill_frontend_processes() -> int:
    """Find and terminate any existing frontend processes to prevent port conflicts."""
    logger.info("Terminating existing frontend processes...")
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd = proc.info['cmdline']
            if cmd:
                cmd_str = " ".join(cmd).lower()
                # Match Node processes running npm or vite for our frontend
                if "node" in proc.info['name'].lower() and ("npm-cli.js" in cmd_str or "vite.js" in cmd_str or "npm run dev" in cmd_str):
                    logger.info(f"Terminating frontend Node process PID {proc.pid}")
                    proc.kill()
                    killed_count += 1
                # Match cmd window running frontend
                elif "cmd.exe" in proc.info['name'].lower() and "npm run dev" in cmd_str and "frontend" in cmd_str:
                    logger.info(f"Terminating frontend CMD terminal process PID {proc.pid}")
                    proc.kill()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return killed_count

def start_backend():
    """Spawn the backend server in a new console window."""
    logger.info("Spawning Backend server...")
    cmd = 'start "Backend - Investment AI" cmd /k venv\\Scripts\\python -m uvicorn api:app --reload --port 8000'
    subprocess.Popen(cmd, shell=True, cwd=BACKEND_DIR)

def start_frontend():
    """Spawn the frontend Vite server in a new console window."""
    logger.info("Spawning Frontend Vite server...")
    cmd = 'start "Frontend - Investment AI" cmd /k npm run dev'
    subprocess.Popen(cmd, shell=True, cwd=FRONTEND_DIR)

def monitor_and_heal():
    """Run a single check and healing cycle."""
    logger.info("=" * 60)
    logger.info("AUTO-HEALING CYCLE INITIATED")
    logger.info("=" * 60)

    # 1. Monitor Backend
    backend_healthy = check_backend_api()
    if backend_healthy:
        logger.info("[OK] Backend API is healthy and responding.")
    else:
        logger.warning("[FAIL] Backend API is down or not responding. Initiating healing...")
        kill_backend_processes()
        time.sleep(2)
        start_backend()
        logger.info("[HEALED] Backend server restart command executed.")

    # 2. Monitor Frontend
    frontend_healthy = check_port(FRONTEND_PORT)
    if frontend_healthy:
        logger.info("[OK] Frontend server is listening on port 5173.")
    else:
        logger.warning("[FAIL] Frontend port 5173 is closed. Initiating healing...")
        kill_frontend_processes()
        time.sleep(2)
        start_frontend()
        logger.info("[HEALED] Frontend server restart command executed.")

    logger.info("=" * 60)
    logger.info("AUTO-HEALING CYCLE COMPLETED")
    logger.info("=" * 60)

if __name__ == "__main__":
    monitor_and_heal()
