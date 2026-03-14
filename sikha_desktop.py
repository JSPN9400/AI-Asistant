from __future__ import annotations

import os
import socket
import threading
import time
import webbrowser
from contextlib import closing
from pathlib import Path
from urllib.request import urlopen

import tkinter as tk
from dotenv import load_dotenv
from tkinter import messagebox

import uvicorn

from assistant.paths import data_dir, env_file_candidates, resource_path


def _find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


class LocalBackend:
    def __init__(self) -> None:
        self.port = _find_free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None
        self._startup_error: Exception | None = None
        self._log_file = self._desktop_log_path()

    def start(self) -> None:
        backend_root = resource_path("backend")
        if str(backend_root) not in os.sys.path:
            os.sys.path.insert(0, str(backend_root))
        bundle_root = resource_path()
        if str(bundle_root) not in os.sys.path:
            os.sys.path.insert(0, str(bundle_root))

        from app.main import app as fastapi_app

        config = uvicorn.Config(
            fastapi_app,
            host="127.0.0.1",
            port=self.port,
            log_level="warning",
            log_config=None,
        )
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        self._wait_until_ready()

    def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _wait_until_ready(self) -> None:
        deadline = time.time() + 15
        while time.time() < deadline:
            if self._startup_error is not None:
                raise RuntimeError(
                    f"Local Sikha backend failed to start. See log: {self._log_file}\n{self._startup_error}"
                ) from self._startup_error
            try:
                with urlopen(f"{self.url}/health", timeout=1) as response:
                    if response.status == 200:
                        return
            except Exception:
                time.sleep(0.2)
        raise RuntimeError(f"Local Sikha backend did not start in time. See log: {self._log_file}")

    def system_status(self) -> dict:
        with urlopen(f"{self.url}/system/status", timeout=5) as response:
            import json

            return json.loads(response.read().decode("utf-8"))

    def _run_server(self) -> None:
        try:
            self._append_log("Starting embedded backend server.")
            assert self._server is not None
            self._server.run()
        except Exception as exc:
            self._startup_error = exc
            self._append_log(f"Backend startup exception: {exc!r}")

    def _append_log(self, message: str) -> None:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        self._log_file.write_text(
            (self._log_file.read_text(encoding="utf-8") if self._log_file.exists() else "")
            + f"[{timestamp}] {message}\n",
            encoding="utf-8",
        )

    @staticmethod
    def _desktop_log_path() -> Path:
        return data_dir() / "desktop-startup.log"


class StartupSplash:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Sikha Desktop")
        self.root.geometry("520x220")
        self.root.resizable(False, False)
        self.root.configure(bg="#f7f2e7")

        self.title_var = tk.StringVar(value="Starting Sikha Desktop")
        self.status_var = tk.StringVar(value="Preparing application...")

        frame = tk.Frame(self.root, bg="#f7f2e7", padx=24, pady=24)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            textvariable=self.title_var,
            font=("Segoe UI Semibold", 18),
            bg="#f7f2e7",
            fg="#1a4038",
        ).pack(anchor="w")

        tk.Label(
            frame,
            text="Launching local backend and connecting to OpenAI.",
            font=("Segoe UI", 10),
            bg="#f7f2e7",
            fg="#5d6258",
        ).pack(anchor="w", pady=(8, 18))

        tk.Label(
            frame,
            textvariable=self.status_var,
            font=("Segoe UI", 11),
            bg="#f7f2e7",
            fg="#195d52",
            wraplength=460,
            justify="left",
        ).pack(anchor="w")

        self.root.update()

    def update(self, message: str) -> None:
        self.status_var.set(message)
        self.root.update_idletasks()
        self.root.update()

    def close(self) -> None:
        try:
            self.root.destroy()
        except tk.TclError:
            pass


def _configure_default_llm() -> None:
    _load_environment()
    os.environ.setdefault("ASSISTANT_ENABLE_CLOUD_REASONER", "true")
    os.environ.setdefault("ASSISTANT_LLM_PROVIDER", "openai")
    os.environ.setdefault("OPENAI_MODEL", "gpt-4.1-mini")


def _ensure_openai_configured() -> None:
    _load_environment()
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if api_key:
        return
    raise RuntimeError(
        "OpenAI is selected as the online LLM, but OPENAI_API_KEY is missing. "
        "Add it in .env or set OPENAI_API_KEY before launching Sikha Desktop."
    )


def _load_environment() -> None:
    for env_path in env_file_candidates():
        load_dotenv(dotenv_path=env_path, override=False)


def main() -> None:
    splash = StartupSplash()

    try:
        splash.update("Configuring OpenAI defaults...")
        _configure_default_llm()

        splash.update("Checking OpenAI configuration...")
        _ensure_openai_configured()

        splash.update("Starting local AI backend...")
        backend = LocalBackend()
        backend.start()

        splash.update("Verifying backend model connection...")
        system_status = backend.system_status()
        llm_status = system_status.get("llm", {})
        if llm_status.get("available") != "true":
            raise RuntimeError(llm_status.get("message", "The backend started, but the LLM is unavailable."))

        splash.update("Launching desktop window...")
    except Exception as exc:
        splash.close()
        messagebox.showerror("Sikha Desktop Startup Failed", str(exc))
        raise SystemExit(1) from exc

    try:
        import webview
    except Exception:
        splash.close()
        webbrowser.open(backend.url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            backend.stop()
        return

    splash.close()
    window = webview.create_window(
        "Sikha Desktop",
        backend.url,
        width=1280,
        height=860,
        min_size=(980, 700),
        text_select=True,
    )

    def on_closed() -> None:
        backend.stop()

    window.events.closed += on_closed
    webview.start()


if __name__ == "__main__":
    main()
