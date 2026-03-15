# Sikha Assistant

**Sikha** is a modular desktop voice assistant for Windows with support for Hindi/English/Hinglish commands, local memory (notes/tasks/command history), web actions, Gmail integration, and basic vision.

---

## ✅ What the Assistant Does

### Core Capabilities
- Voice input using **Vosk** (Hindi/English models)
- Text input fallback (works without audio devices)
- Wake-word mode ("Sikha/Shikha") to ignore background speech
- Command learning (repeats improve recognition)

### Built-in Actions
- Open/close applications (e.g., `open chrome`, `close spotify`)
- Open websites or search engines (e.g., `youtube`, `google`)
- Search Google and YouTube (e.g., `search google for ...`, `search youtube for ...`)
- Play YouTube videos (`play youtube ...`)
- Take screenshots
- Notes: create / list
- Tasks: create / list / complete
- Gmail: read/send emails (requires OAuth setup)
- Vision: describe your webcam scene

---

## 🛠️ Requirements

- Windows (desktop-focused, uses Windows TTS/COM and audio APIs)
- Python 3.11+
- A virtual environment is recommended

---

## 🚀 Quick Start (Windows)

### 1) Create & activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

### 3) (Optional) Configure environment variables

Create a `.env` file in the repo root to persist settings.

Example `.env`:

```env
# --- Voice / input mode ---
# Force text-only mode (disables voice input)
# ASSISTANT_TEXT_MODE=1

# Require wake word ("Sikha" / "Shikha") to accept speech
# ASSISTANT_REQUIRE_WAKE_WORD=1

# Choose a Vosk model folder under `models/`
# ASSISTANT_STT_MODEL=vosk-hindi-en

# --- Cloud reasoner (optional) ---
# ASSISTANT_ENABLE_CLOUD_REASONER=true
# ASSISTANT_LLM_PROVIDER=gemini
# GEMINI_API_KEY=your_key_here

# Or using Ollama:
# ASSISTANT_LLM_PROVIDER=ollama
# OLLAMA_MODEL=phi3
# OLLAMA_HOST=http://127.0.0.1:11434
```

> The app loads `.env` automatically using `python-dotenv`.

### 4) Download a Vosk speech model (voice input)

Put one of the supported model folders inside `models/`, e.g:

- `models/vosk-hindi-en/`
- `models/vosk-model-small-hi-0.22/`
- `models/vosk-model-small-en-us-0.15/`

If no model is found, the assistant will still run in text mode.

### 5) Run the assistant

```powershell
.\.venv\Scripts\python.exe main.py
```

---

## 🗣️ Voice vs Text Modes

- **Default:** Voice input (if Vosk model and microphone available) + text fallback
- **Text-only:** Set `ASSISTANT_TEXT_MODE=1`
- **Wake-word mode:** Set `ASSISTANT_REQUIRE_WAKE_WORD=1` (only processes speech containing "Sikha/Shikha")

---

## 💬 Example Commands

### General / App Actions
- `Sikha open chrome`
- `Sikha close spotify`
- `open youtube`
- `open https://example.com`

### Search
- `Google pe python course search karo`
- `Search google for weather forecast`
- `YouTube pe lo-fi music search karo`
- `Play youtube lo-fi music`

### Notes
- `Create a note: buy milk tomorrow`
- `Note banao: kal subah call kar lena`
- `List notes`

### Tasks
- `Create task: finish report`
- `List tasks`
- `Complete task 3`

### Screenshots
- `Take screenshot`

### Gmail (requires OAuth setup)
- `Read emails`
- `Send email to alice@example.com subject Hi body Hello there`

### Vision (webcam)
- `Describe scene`

---

## 🔌 Optional Integrations

### Gmail (OAuth)
1. Place Google credentials JSON at `credentials.json` in the repo root.
2. Run a Gmail command; the assistant will open a browser to authenticate.

### Vision (webcam)
- Connect a webcam and allow camera access.
- Uses OpenCV to capture a frame and describe it.

### Cloud LLM Reasoner (Gemini / Ollama)
- Enable with `ASSISTANT_ENABLE_CLOUD_REASONER=true`
- Set provider with `ASSISTANT_LLM_PROVIDER=gemini` or `ollama`
- Configure API keys/host as described above

---

## 📦 Install on Another System

### Option 1: Install via pip

```powershell
pip install .
sikha
```

This installs a `sikha` CLI entry point.

### Option 2: Build a Windows executable

```powershell
.\scripts\build_windows.ps1
```

- Output: `dist/SikhaAssistant.exe`

Installer (requires Inno Setup):

```powershell
.\scripts\build_windows.ps1 -Installer
```

---

## 🗃️ Data Storage

- Default data folder: `%LOCALAPPDATA%\SikhaAssistant`
- SQLite memory file: `assistant_memory.db`
- Screenshots and browser TTS resources stored in the same folder

---

## 🧪 Backend Starter (Cloud Work Assistant)

This repo includes a starter FastAPI backend and web UI under `backend/` and `frontend/web/`.

### Run the backend locally

```powershell
cd backend
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONPATH="$(pwd)"
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Then open: `http://127.0.0.1:8000/`

---

## 📚 Documentation & Guides

- [Architecture overview](docs/PRODUCT_ARCHITECTURE.md)
- [Low-spec assistant blueprint](docs/LOW_SPEC_WORK_ASSISTANT_BLUEPRINT.md)
- [AWS EC2 deployment](docs/AWS_EC2_DEPLOYMENT.md)
- [Render deployment](docs/RENDER_DEPLOYMENT.md)

---

## 🛠️ Troubleshooting Tips

- **Missing Vosk model:** Download and place a Vosk model under `models/`
- **Voice TTS not working:** Ensure Windows TTS is enabled or use browser-based TTS fallback
- **Audio device issues:** Check microphone permissions and that audio input is correctly selected

---

## 🙌 Want to Help?
Contributions are welcome! If you find bugs or want new features, open an issue or submit a PR.

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

