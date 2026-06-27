# Sikha Assistant

Sikha is a Windows-first AI assistant project with three main surfaces:

1. `Desktop assistant`
2. `Embedded web dashboard`
3. `FastAPI backend with plugin-based task routing`

It supports voice and text interaction, local desktop actions, memory, screenshots, web search helpers, Gmail actions, basic webcam description, and a work-assistant dashboard with switchable LLM providers.

## What This App Can Do

### Desktop assistant
- Listen to Hindi, English, and Hinglish-style commands
- Accept typed commands when voice is unavailable
- Speak replies using local/browser TTS fallback
- Open apps like Chrome, Notepad, Calculator, File Explorer
- Open Office apps like Excel, Word, and PowerPoint
- Open local files and folders through the OS
- Open websites and search pages
- Search Google and YouTube
- Play YouTube results in the browser
- Take screenshots
- Create notes
- Create, list, and complete tasks
- Read and send Gmail messages after OAuth setup
- Describe the webcam scene

### Web dashboard
- Chat-style UI similar to a modern AI dashboard
- Send task requests to the backend
- See task history
- Upload files into a workspace
- Switch LLM provider and model from the dashboard
- Check whether the selected model is `ready`, `offline`, `missing_key`, `missing_model`, `disabled`, or `exhausted`
- Use work plugins like email drafting, meeting summary, sales report generation, spreadsheet analysis, and browser guidance

### Backend
- FastAPI API for auth, tasks, file upload, plugin listing, and system status
- Plugin discovery system under [backend/app/plugins](/e:/My%20project%20with%20git/AI-Asistant/backend/app/plugins)
- Workspace-aware task routing and task history
- Local SQLite storage by default
- Configurable LLM gateway for `ollama`, `openai`, and `gemini`

## What It Cannot Fully Do Yet

- The web dashboard cannot control your local computer directly
- The web dashboard cannot open your local Excel/Word/Chrome apps
- Full Excel automation is not complete yet
- It does not yet do full "search internet, collect data, open Excel, fill workbook automatically" end-to-end
- Browser automation still depends on Selenium/ChromeDriver for some actions

So if you ask:

- `open excel`
  Desktop app: `yes`
  Web dashboard: `no`
- `open C:\Users\...\report.xlsx`
  Desktop app: `yes`, if the path exists
  Web dashboard: `no`
- `search human growth index and create the table inside Excel automatically`
  Current state: `not fully yet`

## App Modes

### 1. Desktop mode
Runs the Windows assistant directly.

Main files:
- [main.py](/e:/My%20project%20with%20git/AI-Asistant/main.py)
- [assistant/runtime.py](/e:/My%20project%20with%20git/AI-Asistant/assistant/runtime.py)
- [sikha_gui.py](/e:/My%20project%20with%20git/AI-Asistant/sikha_gui.py)
- [sikha_desktop.py](/e:/My%20project%20with%20git/AI-Asistant/sikha_desktop.py)

### 2. Web dashboard mode
Runs the backend and serves the web app from the backend root.

Main files:
- [backend/app/main.py](/e:/My%20project%20with%20git/AI-Asistant/backend/app/main.py)
- [frontend/web/app/index.html](/e:/My%20project%20with%20git/AI-Asistant/frontend/web/app/index.html)
- [frontend/web/app/app.js](/e:/My%20project%20with%20git/AI-Asistant/frontend/web/app/app.js)

## Full Function List

### Voice and speech
- Speech-to-text through Vosk models
- Text fallback if mic/model is missing
- Wake-word support
- Female-voice preference support through TTS settings
- Browser TTS fallback when native voice backend fails

Relevant files:
- [voice/speech_to_text.py](/e:/My%20project%20with%20git/AI-Asistant/voice/speech_to_text.py)
- [voice/text_to_speech.py](/e:/My%20project%20with%20git/AI-Asistant/voice/text_to_speech.py)

### System control
- Open application by name
- Close application by name
- Open local file path
- Open local folder path
- Open Office applications
- Take screenshot

Relevant files:
- [actions/system_actions.py](/e:/My%20project%20with%20git/AI-Asistant/actions/system_actions.py)

### Web actions
- Google search
- Open links
- Read page title
- Browser-based helpers

Relevant files:
- [actions/web_actions.py](/e:/My%20project%20with%20git/AI-Asistant/actions/web_actions.py)
- [integrations/browser/selenium_client.py](/e:/My%20project%20with%20git/AI-Asistant/integrations/browser/selenium_client.py)

### Memory
- Create notes
- List notes
- Create tasks
- List tasks
- Complete tasks
- Persist assistant memory to SQLite

Relevant files:
- [actions/memory_actions.py](/e:/My%20project%20with%20git/AI-Asistant/actions/memory_actions.py)
- [memory/sqlite_store.py](/e:/My%20project%20with%20git/AI-Asistant/memory/sqlite_store.py)

### Gmail
- Read emails
- Send emails
- OAuth-based Google authentication

Relevant files:
- [actions/gmail_actions.py](/e:/My%20project%20with%20git/AI-Asistant/actions/gmail_actions.py)
- [integrations/google/gmail_client.py](/e:/My%20project%20with%20git/AI-Asistant/integrations/google/gmail_client.py)
- [integrations/google/auth.py](/e:/My%20project%20with%20git/AI-Asistant/integrations/google/auth.py)

### Vision
- Capture webcam frame
- Describe scene
- Object/visual helper modules

Relevant files:
- [vision/vision_actions.py](/e:/My%20project%20with%20git/AI-Asistant/vision/vision_actions.py)
- [vision/camera.py](/e:/My%20project%20with%20git/AI-Asistant/vision/camera.py)

### LLM
- Local Ollama support
- OpenAI support
- Gemini support
- Dashboard model switching
- Backend model health check

Relevant files:
- [brain/llm_client.py](/e:/My%20project%20with%20git/AI-Asistant/brain/llm_client.py)
- [backend/app/services/llm_gateway.py](/e:/My%20project%20with%20git/AI-Asistant/backend/app/services/llm_gateway.py)
- [backend/app/api/routes_system.py](/e:/My%20project%20with%20git/AI-Asistant/backend/app/api/routes_system.py)

## Backend Plugins

Current work-assistant plugins discovered from [backend/app/plugins](/e:/My%20project%20with%20git/AI-Asistant/backend/app/plugins):

- `general_assistant`
  Answers normal user questions through the configured LLM
- `small_talk`
  Greetings and simple assistant replies
- `browser_navigator`
  Open URL, Google search, YouTube search, YouTube play
- `web_search`
  Operational web-search style requests
- `email_writer`
  Draft workplace emails and client responses
- `meeting_notes_summarizer`
  Summaries and action items from raw notes
- `sales_report_generator`
  Generate sales-style reports
- `excel_data_analyzer`
  Analyze uploaded spreadsheet data
- `desktop_control`
  Explains that local device control needs the desktop app

## Admin Access and Login

### Important clarification
Right now this project does not have a separate full admin panel with user management screens.

What it does have:
- a demo seeded user
- workspace membership
- role in JWT or headers
- API-key based access for quick local usage

### Default demo login
The backend seeds this demo account automatically from [backend/app/db/session.py](/e:/My%20project%20with%20git/AI-Asistant/backend/app/db/session.py):

- Email: `demo@company.com`
- Password: `demo-pass`
- Workspace: `demo-workspace`
- Role: `manager`

### Login by API
Endpoint:

```http
POST /auth/login
```

JSON body:

```json
{
  "email": "demo@company.com",
  "password": "demo-pass",
  "workspace_id": "demo-workspace"
}
```

Response:
- bearer token
- workspace id
- user id
- role

### Access without bearer login
For local/demo use, backend routes also allow `X-API-Key`.

Default current value from config:

```text
replace-in-prod
```

This is defined in [backend/app/config.py](/e:/My%20project%20with%20git/AI-Asistant/backend/app/config.py) as `ASSISTANT_API_KEY`.

### How to change admin-like access
If you want real admin control later, we can add:

1. user creation
2. role-based admin panel
3. workspace management
4. plugin enable/disable controls
5. audit logs in UI

Right now "admin access" mostly means:
- using the demo manager login
- using bearer token auth
- or using the API key for local dashboard/API access

## LLM Selection

The dashboard now supports selecting:
- `ollama`
- `openai`
- `gemini`

It also supports:
- model name entry
- cloud reasoner on or off
- auto routing on or off
- live check of provider state

### Current recommended local setup
If you want fully local use without cloud billing:

```env
ASSISTANT_ENABLE_CLOUD_REASONER=true
ASSISTANT_LLM_PROVIDER=ollama
OLLAMA_MODEL=phi3:mini
OLLAMA_HOST=http://127.0.0.1:11434
```

## Quick Start

### Requirements
- Windows is the main target
- Python 3.11+
- Virtual environment recommended
- Ollama installed if you want local LLM

### Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run desktop app

```powershell
.\run_sikha.bat
```

Or:

```powershell
.\.venv\Scripts\python.exe sikha_desktop.py
```

### Run console assistant

```powershell
.\.venv\Scripts\python.exe main.py
```

### Run backend + web dashboard

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/
```

If import issues appear from repo root, use:

```powershell
$env:PYTHONPATH="E:\My project with git\AI-Asistant\backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Example Commands

### Desktop commands
- `open chrome`
- `open excel`
- `open word`
- `open C:\Users\YourName\Documents\report.xlsx`
- `open E:\My project with git\AI-Asistant\README.md`
- `close chrome`
- `take screenshot`
- `search google for python tutorial`
- `play youtube lofi music`
- `create note buy milk`
- `create task finish monthly report`
- `list tasks`
- `complete task 1`
- `read emails`
- `describe scene`

### Work-assistant style prompts
- `write an email to my manager about today's status`
- `summarize these meeting notes`
- `analyze this excel file`
- `generate a weekly sales report`
- `search the web for latest hiring trends`

## File Upload and Workspace Use

The web dashboard supports file upload by workspace through:

- `POST /files/upload`

Uploaded files are stored under the project storage area and linked to the workspace.

## API Endpoints

Main routes:
- `GET /health`
- `POST /auth/login`
- `GET /system/status`
- `GET /system/llm`
- `POST /system/llm`
- `POST /system/llm/check`
- `POST /tasks/`
- `GET /tasks/history`
- `GET /plugins/`
- `POST /files/upload`

## Tests

Run backend tests:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
```

## Troubleshooting

### App says model is unavailable
- Check Ollama is running
- Check selected model exists in Ollama
- Check dashboard provider/model selection

### Desktop says app or file cannot open
- Confirm path exists
- Confirm Windows has an associated app for the file
- For Office files, confirm Office is installed

### Web dashboard cannot open local apps
- This is expected
- Use the desktop assistant for local OS actions

### OpenAI or Gemini problems
- Check API key
- Check selected provider
- Check whether quota is exhausted

## Project Structure

- [actions](/e:/My%20project%20with%20git/AI-Asistant/actions)
  Desktop/local actions
- [assistant](/e:/My%20project%20with%20git/AI-Asistant/assistant)
  Runtime, routing, path helpers
- [backend](/e:/My%20project%20with%20git/AI-Asistant/backend)
  FastAPI backend and plugins
- [frontend/web](/e:/My%20project%20with%20git/AI-Asistant/frontend/web)
  Browser dashboard
- [memory](/e:/My%20project%20with%20git/AI-Asistant/memory)
  Local memory store
- [vision](/e:/My%20project%20with%20git/AI-Asistant/vision)
  Camera and scene helpers
- [voice](/e:/My%20project%20with%20git/AI-Asistant/voice)
  STT and TTS

## Next Good Upgrades

If you want, the next useful improvements would be:

1. real admin panel
2. Excel automation
3. internet data extraction into spreadsheet
4. better web automation fallback without Selenium dependency
5. persistent multi-message chat timeline in the dashboard
