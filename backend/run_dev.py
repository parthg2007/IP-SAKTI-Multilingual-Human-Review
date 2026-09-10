#!/usr/bin/env python3
"""
IP-SAKTI Full-Stack Unified Development Runner.

Launches both the FastAPI backend and Vite React frontend concurrently
with coordinated process lifecycle management and unified logging.

Usage:
  python3 run_dev.py             # Run both backend & frontend in dev mode
  python3 run_dev.py --build     # Build frontend first, then run dev servers
  python3 run_dev.py --prod      # Build frontend and serve everything on port 8000 via FastAPI
"""

import os
import sys
import time
import signal
import argparse
import subprocess
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = BASE_DIR / "frontend"


# Terminal ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def log_pipe(pipe, prefix, color):
    """Stream subprocess output with a colored prefix."""
    try:
        for line in iter(pipe.readline, ''):
            if not line:
                break
            clean_line = line.rstrip('\r\n')
            if clean_line:
                print(f"{color}{prefix}{RESET} {clean_line}", flush=True)
    except Exception:
        pass
    finally:
        pipe.close()


def run_command(cmd, cwd=BASE_DIR, check=True):
    """Run a synchronous shell command."""
    print(f"{YELLOW}> Running:{RESET} {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if check and result.returncode != 0:
        print(f"{RED}Command failed with exit code {result.returncode}{RESET}")
        sys.exit(result.returncode)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="IP-SAKTI Full-Stack Runner")
    parser.add_argument("--prod", action="store_true", help="Serve full-stack from FastAPI on port 8000")
    parser.add_argument("--build", action="store_true", help="Build frontend before starting dev servers")
    parser.add_argument("--backend-port", type=int, default=8000, help="Port for backend server (default: 8000)")
    parser.add_argument("--frontend-port", type=int, default=5173, help="Port for Vite dev server (default: 5173)")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print(f"{BOLD}🌿 IP-SAKTI Full-Stack Platform Launcher{RESET}")
    print("=" * 70)

    # Verify frontend directory exists
    if not FRONTEND_DIR.exists():
        print(f"{RED}Error: Frontend directory not found at {FRONTEND_DIR}{RESET}")
        sys.exit(1)

    # Check node_modules
    if not (FRONTEND_DIR / "node_modules").exists():
        print(f"{YELLOW}node_modules not found. Running 'npm install' in frontend...{RESET}")
        run_command(["npm", "install"], cwd=FRONTEND_DIR)

    # Production / Standalone mode
    if args.prod:
        print(f"\n{BOLD}Building frontend for production...{RESET}")
        run_command(["npm", "run", "build"], cwd=FRONTEND_DIR)
        print(f"\n{GREEN}{BOLD}Starting unified IP-SAKTI server on http://127.0.0.1:{args.backend_port}{RESET}")
        print(f"Web UI & API are both served on: http://127.0.0.1:{args.backend_port}")
        print(f"API Docs available at: http://127.0.0.1:{args.backend_port}/docs\n")
        cmd = [
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", "0.0.0.0", "--port", str(args.backend_port)
        ]
        try:
            subprocess.run(cmd, cwd=BASE_DIR)
        except KeyboardInterrupt:
            print("\nShutting down IP-SAKTI server.")
        return

    # If --build was requested in dev mode
    if args.build:
        print(f"\n{BOLD}Pre-building frontend...{RESET}")
        run_command(["npm", "run", "build"], cwd=FRONTEND_DIR)

    # Start Dev Servers concurrently
    print(f"\n{CYAN}Starting Backend (FastAPI) on http://127.0.0.1:{args.backend_port}{RESET}")
    print(f"{GREEN}Starting Frontend (Vite) on http://localhost:{args.frontend_port}{RESET}")
    print(f"{YELLOW}Press Ctrl+C at any time to stop both servers.{RESET}\n")

    backend_env = os.environ.copy()
    backend_env["PORT"] = str(args.backend_port)

    backend_cmd = [
        sys.executable, "-m", "uvicorn", "app.main:app",
        "--host", "0.0.0.0", "--port", str(args.backend_port), "--reload"
    ]

    frontend_cmd = ["npm", "run", "dev", "--", "--port", str(args.frontend_port)]

    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=BASE_DIR,
        env=backend_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Spawn daemon reader threads for output
    t_back = threading.Thread(target=log_pipe, args=(backend_proc.stdout, "[BACKEND]", CYAN), daemon=True)
    t_front = threading.Thread(target=log_pipe, args=(frontend_proc.stdout, "[FRONTEND]", GREEN), daemon=True)
    t_back.start()
    t_front.start()

    def shutdown(signum=None, frame=None):
        print(f"\n{YELLOW}Stopping IP-SAKTI services...{RESET}")
        for p in (frontend_proc, backend_proc):
            try:
                p.terminate()
            except Exception:
                pass
        time.sleep(0.5)
        for p in (frontend_proc, backend_proc):
            try:
                p.kill()
            except Exception:
                pass
        print(f"{GREEN}All services stopped cleanly. Goodbye!{RESET}")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Monitor processes
    while True:
        b_code = backend_proc.poll()
        f_code = frontend_proc.poll()
        if b_code is not None:
            print(f"{RED}Backend process exited unexpectedly with code {b_code}{RESET}")
            shutdown()
        if f_code is not None:
            print(f"{RED}Frontend process exited unexpectedly with code {f_code}{RESET}")
            shutdown()
        time.sleep(0.5)


if __name__ == "__main__":
    main()
