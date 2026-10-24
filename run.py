"""Run FastAPI and the existing Lovable frontend with one command.

Development launcher: FastAPI at 127.0.0.1:8000 and Vite at 127.0.0.1:5173.
The Vite dev server proxies /api to FastAPI. No CORS configuration needed.
"""

import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent


def main() -> None:
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if npm is None:
        raise SystemExit("npm not found. Install Node.js and reopen your terminal.")

    frontend_env = os.environ.copy()
    frontend_env["VITE_API_MODE"] = "http"

    # Separate process groups make clean shutdown possible on macOS/Linux.
    platform_options = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=ROOT,
        **platform_options,
    )
    frontend = None
    try:
        frontend = subprocess.Popen(
            [npm, "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173", "--strictPort"],
            cwd=ROOT,
            env=frontend_env,
            **platform_options,
        )
        print("\nOpen http://127.0.0.1:5173 in your browser.\n", flush=True)
        while backend.poll() is None and frontend.poll() is None:
            time.sleep(0.4)
    except KeyboardInterrupt:
        pass
    finally:
        for proc in (frontend, backend):
            if proc is None or proc.poll() is not None:
                continue
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            else:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass


if __name__ == "__main__":
    main()
