"""
GeneGraph — Full-Stack Runner Script
Starts both the FastAPI backend and Vite React frontend concurrently.
Handles graceful shutdown (Ctrl+C), process cleanup, and service pre-checks.

Usage:
    python run.py
    python run.py --backend-only
    python run.py --frontend-only
    python run.py --no-browser
"""

import sys
import os
import socket
import subprocess
import threading
import time
import signal
import webbrowser
import argparse
from pathlib import Path

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    os.system("")

# ANSI Color codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

processes: list[subprocess.Popen] = []
shutdown_event = threading.Event()


def log_system(msg: str):
    print(f"{MAGENTA}{BOLD}[SYSTEM]{RESET} {msg}", flush=True)


def log_backend(msg: str):
    print(f"{CYAN}[BACKEND]{RESET} {msg}", end="", flush=True)


def log_frontend(msg: str):
    print(f"{GREEN}[FRONTEND]{RESET} {msg}", end="", flush=True)


def check_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a TCP port is listening."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def find_python_interpreter() -> str:
    """Find the best Python executable that has the required backend packages."""
    candidates = []

    # 1. Project virtual environment
    if sys.platform == "win32":
        venv_py = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    else:
        venv_py = ROOT_DIR / ".venv" / "bin" / "python"
    
    if venv_py.exists():
        candidates.append(str(venv_py))

    # 2. Current executing python
    candidates.append(sys.executable)

    # 3. Fallback generic
    candidates.append("python")

    for py in candidates:
        try:
            res = subprocess.run(
                [py, "-c", "import uvicorn, fastapi; print('OK')"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            if res.returncode == 0 and "OK" in res.stdout:
                return py
        except Exception:
            continue

    return sys.executable


def stream_output(pipe, log_func):
    """Stream process output line-by-line to stdout with prefix."""
    try:
        for line in iter(pipe.readline, ""):
            if shutdown_event.is_set():
                break
            if line:
                log_func(line)
    except Exception:
        pass
    finally:
        pipe.close()


def kill_process_tree(proc: subprocess.Popen):
    """Cleanly terminate a process and all its children across OSes."""
    if proc.poll() is not None:
        return

    pid = proc.pid
    if sys.platform == "win32":
        # Forcefully terminate process tree on Windows to free up ports
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
        except Exception:
            proc.kill()
    else:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception:
            proc.terminate()


def cleanup(*args):
    """Cleanup hook for graceful termination."""
    if shutdown_event.is_set():
        return
    shutdown_event.set()
    print()
    log_system(f"{YELLOW}Shutting down servers gracefully...{RESET}")

    for proc in processes:
        kill_process_tree(proc)

    log_system(f"{GREEN}All services stopped. Goodbye! 👋{RESET}")
    sys.exit(0)


def preflight_checks():
    """Check common prerequisites like MongoDB and Neo4j, giving helpful hints."""
    print("=" * 70)
    print(f"{CYAN}{BOLD}🧬  GeneGraph — AI-Powered Knowledge Graph Explorer{RESET}")
    print("=" * 70)

    # Read .env for Neo4j URI
    neo4j_uri = "bolt://localhost:7687"
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        try:
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("NEO4J_URI="):
                        neo4j_uri = line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass

    # Check MongoDB (Auth store)
    mongo_running = check_port_open("localhost", 27017, timeout=0.8)
    if mongo_running:
        log_system(f"{GREEN}MongoDB: Running on localhost:27017 (Auth ready ✅){RESET}")
    else:
        log_system(f"{YELLOW}MongoDB: Not detected on localhost:27017{RESET}")
        log_system(f"{DIM}  ↳ Note: User login/registration requires MongoDB.{RESET}")
        log_system(f"{DIM}  ↳ Tip: Start via local MongoDB service or Docker: 'docker run -d -p 27017:27017 mongo'{RESET}")

    # Check Neo4j
    if "databases.neo4j.io" in neo4j_uri or "neo4j+s://" in neo4j_uri or "neo4j+ssc://" in neo4j_uri:
        host = neo4j_uri.split("://")[-1].split(":")[0].split("/")[0]
        log_system(f"{GREEN}Neo4j: Configured for Neo4j Aura Cloud ({host}) ☁️ ✅{RESET}")
    else:
        neo4j_running = check_port_open("localhost", 7687, timeout=0.8)
        if neo4j_running:
            log_system(f"{GREEN}Neo4j: Running on localhost:7687 (Graph DB ready ✅){RESET}")
        else:
            log_system(f"{YELLOW}Neo4j: Not detected on localhost:7687{RESET}")
            log_system(f"{DIM}  ↳ Note: Graph queries will fail without Neo4j, but UI & Auth will run.{RESET}")

    print("-" * 70)


def main():
    parser = argparse.ArgumentParser(description="Start GeneGraph Full-Stack App")
    parser.add_argument("--backend-only", action="store_true", help="Start only FastAPI backend")
    parser.add_argument("--frontend-only", action="store_true", help="Start only Vite frontend")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    parser.add_argument("--port", type=int, default=8000, help="Backend port (default: 8000)")
    args = parser.parse_args()

    # Register termination signals
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    preflight_checks()

    # 1. Start Backend
    if not args.frontend_only:
        python_exe = find_python_interpreter()
        log_system(f"Using Python: {CYAN}{python_exe}{RESET}")
        log_system(f"Starting Backend on {BOLD}http://localhost:{args.port}{RESET} ...")

        backend_cmd = [
            python_exe,
            "-m",
            "uvicorn",
            "app.main:app",
            "--reload",
            "--port",
            str(args.port),
        ]

        try:
            backend_proc = subprocess.Popen(
                backend_cmd,
                cwd=str(BACKEND_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            processes.append(backend_proc)
            threading.Thread(
                target=stream_output,
                args=(backend_proc.stdout, log_backend),
                daemon=True,
            ).start()
        except Exception as e:
            log_system(f"{RED}Failed to start backend: {e}{RESET}")
            sys.exit(1)

    # 2. Start Frontend
    if not args.backend_only:
        log_system(f"Starting Frontend on {BOLD}http://localhost:5173{RESET} ...")

        # Use npm.cmd on Windows, npm on Unix
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        frontend_cmd = [npm_cmd, "run", "dev"]

        try:
            frontend_proc = subprocess.Popen(
                frontend_cmd,
                cwd=str(FRONTEND_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            processes.append(frontend_proc)
            threading.Thread(
                target=stream_output,
                args=(frontend_proc.stdout, log_frontend),
                daemon=True,
            ).start()
        except Exception as e:
            log_system(f"{RED}Failed to start frontend: {e}{RESET}")
            cleanup()
            sys.exit(1)

    # Give services a moment to initialize
    time.sleep(2)

    print("\n" + "=" * 70)
    log_system(f"{GREEN}{BOLD}🚀 GeneGraph is running!{RESET}")
    if not args.backend_only:
        log_system(f"🌐 App Frontend:     {BOLD}http://localhost:5173{RESET}")
    if not args.frontend_only:
        log_system(f"⚙️  API & Docs:       {BOLD}http://localhost:{args.port}/docs{RESET}")
        log_system(f"💓 Health Check:     {BOLD}http://localhost:{args.port}/health{RESET}")
    log_system(f"{DIM}Press Ctrl+C at any time to stop all services.{RESET}")
    print("=" * 70 + "\n")

    # Optionally open browser
    if not args.no_browser and not args.backend_only:
        threading.Timer(1.5, lambda: webbrowser.open("http://localhost:5173")).start()

    # Wait for processes
    try:
        while True:
            for proc in processes:
                if proc.poll() is not None:
                    log_system(f"{YELLOW}A process exited with code {proc.returncode}. Stopping all...{RESET}")
                    cleanup()
                    return
            time.sleep(0.5)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
