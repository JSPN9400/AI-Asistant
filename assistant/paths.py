import os
import sys
from pathlib import Path


APP_NAME = "SikhaAssistant"


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def bundled_root() -> Path:
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        return Path(bundle_dir)
    return app_root()


def data_dir() -> Path:
    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata:
        path = Path(local_appdata) / APP_NAME
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except OSError:
            pass

    path = app_root() / ".sikha-data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def resource_path(*parts: str) -> Path:
    candidate = bundled_root().joinpath(*parts)
    if candidate.exists():
        return candidate
    return app_root().joinpath(*parts)
