from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "artifacts" / "local_app"
BACKEND_LOG = ARTIFACTS_DIR / "backend.log"
FRONTEND_LOG = ARTIFACTS_DIR / "frontend.log"


def _url_ready(url: str, timeout_seconds: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
            return 200 <= response.status < 500
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return False


def _wait_for_url(url: str, timeout_seconds: int = 60) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if _url_ready(url):
            return True
        time.sleep(1.0)
    return False


def _start_process(command: list[str], *, env: dict[str, str], log_path: Path) -> subprocess.Popen:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handle = log_path.open("w", encoding="utf-8")
    return subprocess.Popen(
        command,
        cwd=str(ROOT),
        env=env,
        stdout=handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def _terminate_process(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def run_local_app(*, host: str, backend_port: int, frontend_port: int, no_browser: bool = False) -> int:
    backend_url = f"http://{host}:{backend_port}"
    frontend_url = f"http://{host}:{frontend_port}"

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT}:{env.get('PYTHONPATH', '')}".rstrip(":")
    env["DECISION_OS_API_BASE"] = backend_url

    backend_process: subprocess.Popen | None = None
    frontend_process: subprocess.Popen | None = None

    backend_running = _url_ready(f"{backend_url}/system/snapshot")
    frontend_running = _url_ready(frontend_url)

    try:
        if not backend_running:
            backend_process = _start_process(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "backend.main:app",
                    "--host",
                    host,
                    "--port",
                    str(backend_port),
                ],
                env=env,
                log_path=BACKEND_LOG,
            )
            if not _wait_for_url(f"{backend_url}/system/snapshot", timeout_seconds=60):
                raise RuntimeError(f"Backend failed to start. See {BACKEND_LOG}")

        if not frontend_running:
            frontend_process = _start_process(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    str(ROOT / "frontend" / "streamlit_app.py"),
                    "--server.address",
                    host,
                    "--server.port",
                    str(frontend_port),
                    "--browser.gatherUsageStats",
                    "false",
                    "--server.headless",
                    "true",
                ],
                env=env,
                log_path=FRONTEND_LOG,
            )
            if not _wait_for_url(frontend_url, timeout_seconds=90):
                raise RuntimeError(f"Frontend failed to start. See {FRONTEND_LOG}")

        if not no_browser:
            webbrowser.open(frontend_url)

        print(f"Decision OS is running at {frontend_url}")
        print(f"Backend log: {BACKEND_LOG}")
        print(f"Frontend log: {FRONTEND_LOG}")

        if frontend_process is not None:
            return frontend_process.wait()
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        return 0
    finally:
        _terminate_process(frontend_process)
        _terminate_process(backend_process)


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch Decision OS locally as a one-click desktop app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--backend-port", type=int, default=8000)
    parser.add_argument("--frontend-port", type=int, default=8501)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    raise SystemExit(
        run_local_app(
            host=args.host,
            backend_port=args.backend_port,
            frontend_port=args.frontend_port,
            no_browser=args.no_browser,
        )
    )


if __name__ == "__main__":
    main()
