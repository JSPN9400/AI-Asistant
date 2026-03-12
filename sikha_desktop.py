from __future__ import annotations

import os
import socket
import subprocess
import threading
import time
import webbrowser
from contextlib import closing
from urllib.request import Request, urlopen

import uvicorn

from assistant.paths import resource_path


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

    def start(self) -> None:
        backend_root = resource_path("backend")
        if str(backend_root) not in os.sys.path:
            os.sys.path.insert(0, str(backend_root))

        config = uvicorn.Config(
            "app.main:app",
            host="127.0.0.1",
            port=self.port,
            log_level="warning",
        )
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)
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
            try:
                with urlopen(f"{self.url}/health", timeout=1) as response:
                    if response.status == 200:
                        return
            except Exception:
                time.sleep(0.2)
        raise RuntimeError("Local Sikha backend did not start in time.")


def _configure_default_llm() -> None:
    os.environ.setdefault("ASSISTANT_ENABLE_CLOUD_REASONER", "true")
    os.environ.setdefault("ASSISTANT_LLM_PROVIDER", "ollama")
    os.environ.setdefault("OLLAMA_MODEL", "phi3:mini")
    os.environ.setdefault("OLLAMA_HOST", "http://127.0.0.1:11434")


def _ollama_ready(host: str) -> bool:
    try:
        req = Request(f"{host.rstrip('/')}/api/tags", method="GET")
        with urlopen(req, timeout=2) as response:
            return response.status == 200
    except Exception:
        return False


def _ensure_ollama_running() -> None:
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    if _ollama_ready(host):
        return

    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Ollama is not installed. Install Ollama or change the desktop app LLM provider.") from exc

    deadline = time.time() + 20
    while time.time() < deadline:
        if _ollama_ready(host):
            return
        time.sleep(0.5)

    raise RuntimeError("Ollama did not start in time. Start Ollama manually and relaunch Sikha.")


def main() -> None:
    _configure_default_llm()
    _ensure_ollama_running()

    backend = LocalBackend()
    backend.start()

    try:
        import webview
    except Exception:
        webbrowser.open(backend.url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            backend.stop()
        return

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
