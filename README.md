# Sikha Assistant

Sikha is a modular desktop assistant with Hindi/English/Hinglish command parsing, voice-first control, memory, web actions, Gmail hooks, and basic vision support.

## Features

- Voice input with wake-word focus and background filtering
- Hindi, English, and Hinglish command parsing
- Command learning backed by SQLite memory
- Open apps, open websites, search Google/YouTube, take screenshots
- Gmail, notes, tasks, and vision extension points
- Browser-based speech fallback when Windows COM TTS is blocked

## Local Run

1. Create and activate a virtual environment.
2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Optional: set Gemini key in `.env`:

   ```env
   GEMINI_API_KEY=your_key_here
   ```

4. Put a Vosk model under `models/` for voice mode, for example:
   - `models/vosk-hindi-en/`
   - `models/vosk-model-small-hi-0.22/`
   - `models/vosk-model-small-en-us-0.15/`

5. Run:

   ```powershell
   .\.venv\Scripts\python.exe main.py
   ```

6. Text-only mode:

   ```powershell
   $env:ASSISTANT_TEXT_MODE='1'
   .\.venv\Scripts\python.exe main.py
   ```

## Example Commands

- `Sikha youtube kholo`
- `python google pe search karo`
- `open chrome`
- `ek note banao: kal subah call karna`
- `show tasks`

## Install On Another System

You have two supported options.

### Option 1: Install with Python

Copy the project, then run:

```powershell
pip install .
sikha
```

This installs a `sikha` command using `pyproject.toml`.

### Option 2: Build a Windows App

From this project folder:

```powershell
.\scripts\build_windows.ps1
```

Output goes to:

- `dist/SikhaAssistant/` for the folder build
- `dist/SikhaAssistant.exe` if you build with `-OneFile`

One-file build:

```powershell
.\scripts\build_windows.ps1 -OneFile
```

## Portable App Notes

- User data is stored under `%LOCALAPPDATA%\SikhaAssistant`
- SQLite memory database is created automatically there
- Selenium cache is kept in the same user data area
- Screenshots are saved under the app data folder unless you override the path
- Bundled resources like `voice/browser_tts.html` are packaging-safe

## Quick Launcher

Double-click:

```text
run_sikha.bat
```

It uses the local virtual environment if present, otherwise it tries `py`.

## Optional Integrations

- Gmail OAuth: add `credentials.json`
- Vision: add your YOLO model file
- Better voice mode: install a suitable Vosk Hindi/English model

