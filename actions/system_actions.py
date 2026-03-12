import os
import subprocess
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

import psutil

from assistant.paths import data_dir


APP_ALIASES = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "notepad": "notepad",
    "notes": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "command prompt": "cmd",
    "cmd": "cmd",
    "file explorer": "explorer",
    "explorer": "explorer",
}

APP_COMMANDS = {
    "chrome": [r"C:\Program Files\Google\Chrome\Application\chrome.exe"],
    "notepad": ["notepad.exe"],
    "calc": ["calc.exe"],
    "cmd": ["cmd.exe"],
    "explorer": ["explorer.exe"],
}

KNOWN_SITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "github": "https://www.github.com",
}


def open_application(app_name: str) -> str:
    name = APP_ALIASES.get(app_name.lower().strip(), app_name.lower().strip())
    if not name:
        return "I need an application name to open."

    command = APP_COMMANDS.get(name)
    if command is not None:
        try:
            subprocess.Popen(command)
            return f"Opening {app_name}."
        except FileNotFoundError:
            pass

    try:
        subprocess.Popen([app_name])
        return f"Opening {app_name}."
    except FileNotFoundError:
        pass
    except OSError:
        pass

    if hasattr(os, "startfile"):
        try:
            os.startfile(app_name)
            return f"Opening {app_name}."
        except OSError:
            pass

    return f"I don't know how to open {app_name} yet."


def close_application(app_name: str) -> str:
    if not app_name:
        return "I need an application name to close."

    killed = 0
    for proc in psutil.process_iter(["name"]):
        try:
            name = (proc.info["name"] or "").lower()
            if app_name.lower() in name:
                proc.terminate()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed:
        return f"Closed {killed} instances of {app_name}."
    return f"No running {app_name} processes found."


def open_website(url: Optional[str] = None, query: Optional[str] = None) -> str:
    import webbrowser

    if not url and query:
        url = KNOWN_SITES.get(query.lower().strip())
        if url is None:
            url = f"https://www.google.com/search?q={quote_plus(query)}"
    if not url:
        return "I need a URL or a search query."

    webbrowser.open(url)
    return f"Opening {url}"


def youtube_search(query: str) -> str:
    import webbrowser

    if not query:
        return "I need something to search on YouTube."
    url = "https://www.youtube.com/results?search_query=" + query.replace(" ", "+")
    webbrowser.open(url)
    return f"Searching YouTube for {query}"


def youtube_play(query: str) -> str:
    # For now, just open the YouTube search results; you can extend this
    # later with Selenium to auto-play the first result.
    return youtube_search(query)


def take_screenshot(output_dir: str | None = None) -> str:
    try:
        import pyautogui
    except Exception as exc:
        return f"Screenshot is unavailable right now: {exc}"

    path = Path(output_dir) if output_dir else data_dir() / "screenshots"
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / "screenshot.png"
    screenshot = pyautogui.screenshot()
    screenshot.save(file_path)
    return f"Screenshot saved to {file_path}"


def list_files(path: str = ".") -> str:
    try:
        entries = os.listdir(path)
    except FileNotFoundError:
        return f"Path {path} does not exist."
    if not entries:
        return f"No files in {path}."
    return "Files: " + ", ".join(entries)


def create_folder(path: str) -> str:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return f"Folder {p} created."


def delete_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"File {p} does not exist."
    p.unlink()
    return f"Deleted file {p}."

