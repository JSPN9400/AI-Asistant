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

- `dist/SikhaAssistant.exe`

Installable Windows setup:

```powershell
.\scripts\build_windows.ps1 -Installer
```

This requires Inno Setup (`iscc`) to be installed.

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

## Cloud Work Assistant Scaffold

This repo now also contains a starter cloud-first workplace AI architecture under:

- [backend/app/main.py](/e:/My%20project%20with%20git/AI-Asistant/backend/app/main.py)
- [docs/PRODUCT_ARCHITECTURE.md](/e:/My%20project%20with%20git/AI-Asistant/docs/PRODUCT_ARCHITECTURE.md)
- [frontend/web/README.md](/e:/My%20project%20with%20git/AI-Asistant/frontend/web/README.md)

Run the backend locally:

```powershell
cd "e:\My project with git\AI-Asistant\backend"
..\.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONPATH="e:\My project with git\AI-Asistant\backend"
..\.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Optional cloud reasoner setup:

```powershell
$env:ASSISTANT_ENABLE_CLOUD_REASONER="true"
$env:ASSISTANT_LLM_PROVIDER="gemini"
$env:GEMINI_API_KEY="your_key_here"
```

Or for Ollama:

```powershell
$env:ASSISTANT_ENABLE_CLOUD_REASONER="true"
$env:ASSISTANT_LLM_PROVIDER="ollama"
$env:OLLAMA_MODEL="phi3"
$env:OLLAMA_HOST="http://127.0.0.1:11434"
```

Web app:

- After starting the backend, open `http://127.0.0.1:8000/`
- API docs stay available at `http://127.0.0.1:8000/docs`
- Default API key for the starter is `replace-in-prod`

Core starter modules included:

- frontend placeholders for web, desktop, and mobile companion
- FastAPI API server
- task router
- LLM reasoning stub
- plugin system
- auth and workspace stubs
- file upload service
- deployment Docker files

The web starter now includes:

- task runner UI
- plugin catalog view
- task history view
- file upload to workspace storage
- system status view for API and LLM routing mode
- login flow for bearer-token auth using the seeded demo user

Starter login:

```text
email: demo@company.com
password: demo-pass
workspace: demo-workspace
```

Architecture blueprint for the low-spec workplace assistant:

- [docs/LOW_SPEC_WORK_ASSISTANT_BLUEPRINT.md](/e:/My%20project%20with%20git/AI-Asistant/docs/LOW_SPEC_WORK_ASSISTANT_BLUEPRINT.md)
- [docs/AWS_EC2_DEPLOYMENT.md](/e:/My%20project%20with%20git/AI-Asistant/docs/AWS_EC2_DEPLOYMENT.md)
- [docs/RENDER_DEPLOYMENT.md](/e:/My%20project%20with%20git/AI-Asistant/docs/RENDER_DEPLOYMENT.md)

