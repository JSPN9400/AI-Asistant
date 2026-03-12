# Low-Spec AI Work Assistant Blueprint

## 1. Recommended Architecture

Use a cloud-first, thin-client architecture so low-spec laptops, shared desktops, and mobile devices only handle UI, capture, and rendering.

### Core runtime flow

1. User enters text or voice request in web, desktop, or mobile client.
2. Frontend sends request, workspace context, and file references to the API server.
3. API server authenticates the user and validates workspace access.
4. Task router calls the LLM reasoning layer to convert the request into a structured task.
5. Plugin manager selects the correct workplace plugin.
6. Plugin executes business logic and returns structured output.
7. Result is stored in task history, audit logs, and returned to the client.

### Recommended modules

- `frontend`
  Thin client for chat, voice capture, file upload, history, approvals, and workspace switching.
- `api_server`
  FastAPI layer for auth, tasks, plugins, files, and admin APIs.
- `task_router`
  Orchestrates request lifecycle and hands the structured task to the right plugin.
- `llm_reasoning`
  Converts natural language into structured JSON instructions.
- `task_plugins`
  Domain tools such as sales report generation, email drafting, and spreadsheet analysis.
- `database`
  Stores users, workspaces, task runs, uploaded files, and audit metadata.
- `authentication`
  Supports API keys for service access and JWT/session auth for end users.
- `logging`
  Structured logs, audit trails, latency metrics, and plugin execution traces.

### Commercial-readiness decisions

- Multi-tenant isolation at the workspace level
- Role-based access for employee, manager, admin
- API authentication and service-to-service keys
- Audit logs for task runs and file access
- File storage separated by workspace
- LLM calls routed through a server-side gateway so client devices never hold secrets
- Queue-based execution path for heavier tasks like spreadsheet analysis or long reports

### Suggested production stack

- Frontend: React or Next.js web app
- Desktop: Tauri shell around the web UI
- Mobile companion: Flutter or React Native
- API: FastAPI
- Queue/cache: Redis
- Database: PostgreSQL
- File storage: S3, Azure Blob, or GCS
- LLM gateway: OpenAI, Azure OpenAI, Gemini, or self-hosted inference behind one adapter
- Observability: OpenTelemetry, structured JSON logs, centralized log storage

## 2. Recommended Folder Structure

```text
backend/
  app/
    api/
      routes_auth.py
      routes_files.py
      routes_plugins.py
      routes_tasks.py
    core/
      auth.py
      logging.py
      security.py
      workspace.py
    db/
      models.py
      session.py
      repositories/
    plugins/
      base.py
      email_writer.py
      excel_data_analyzer.py
      meeting_notes_summarizer.py
      sales_report_generator.py
      web_search.py
    schemas/
      auth.py
      plugin.py
      task.py
    services/
      audit_service.py
      file_service.py
      llm_reasoner.py
      plugin_manager.py
      task_router.py
    workers/
      jobs.py
    config.py
    main.py
  tests/
frontend/
  web/
  desktop/
  mobile_companion/
docs/
infra/
  docker/
```

## 3. Python Backend Skeleton

The repo already includes the requested backend skeleton.

### API server

- Entry point: [backend/app/main.py](/e:/My%20project%20with%20git/AI-Asistant/backend/app/main.py)
- Exposes `auth`, `tasks`, `plugins`, and `files`
- Mounts the lightweight web frontend for a simple single-deploy setup

### Task router

- Orchestration: [backend/app/services/task_router.py](/e:/My%20project%20with%20git/AI-Asistant/backend/app/services/task_router.py)
- Responsibilities:
  - validate workspace access
  - run LLM reasoning
  - pick plugin
  - execute task
  - persist history
  - emit audit events

### LLM reasoning

- Starter implementation: [backend/app/services/llm_reasoner.py](/e:/My%20project%20with%20git/AI-Asistant/backend/app/services/llm_reasoner.py)
- Current behavior:
  - maps workplace language into `StructuredTask`
  - can be replaced with a cloud LLM call without changing the router contract

### Plugin system

- Base contract: [backend/app/plugins/base.py](/e:/My%20project%20with%20git/AI-Asistant/backend/app/plugins/base.py)
- Discovery manager: [backend/app/services/plugin_manager.py](/e:/My%20project%20with%20git/AI-Asistant/backend/app/services/plugin_manager.py)
- Design intent:
  - add a new file under `backend/app/plugins/`
  - subclass `BasePlugin`
  - expose `name`, `description`, `supported_actions`
  - the manager auto-discovers it

### Data and security layers

- Auth stub: [backend/app/core/auth.py](/e:/My%20project%20with%20git/AI-Asistant/backend/app/core/auth.py)
- Models: [backend/app/db/models.py](/e:/My%20project%20with%20git/AI-Asistant/backend/app/db/models.py)
- Config: [backend/app/config.py](/e:/My%20project%20with%20git/AI-Asistant/backend/app/config.py)

## 4. Example Plugin Implementation

Use [backend/app/plugins/sales_report_generator.py](/e:/My%20project%20with%20git/AI-Asistant/backend/app/plugins/sales_report_generator.py) as the reference plugin.

It demonstrates the core commercial plugin pattern:

- declarative metadata for cataloging and routing
- structured input contract
- file-aware execution using uploaded attachments
- structured output with report body, highlights, and recommended actions

Example structured task generated by the reasoner:

```json
{
  "task": "sales_report_generator",
  "parameters": {
    "data_source": "uploaded_file",
    "format": "professional_report",
    "period": "weekly",
    "audience": "sales_manager"
  }
}
```

## 5. Deployment Explanation

### Web application

- Primary deployment target for office workers
- Deploy FastAPI and static frontend together in one container for simplicity
- Good for browser-based access on old company laptops and thin clients

### Desktop app

- Use Tauri so RAM and CPU usage stay lower than Electron
- Desktop app wraps the web frontend and calls the same API server
- Add optional local features like microphone capture, system tray, and notifications

### Mobile companion

- Keep mobile focused on quick approvals, voice capture, alerts, and simple task submission
- Heavy task generation still runs in the cloud

### Infra deployment pattern

- Containerize backend with Docker
- Run API behind a reverse proxy or ingress
- Use Redis for queueing long-running tasks
- Use PostgreSQL for operational data
- Store uploads in object storage
- Keep LLM credentials only on the server side

Starter infrastructure files:

- [infra/docker/Dockerfile.backend](/e:/My%20project%20with%20git/AI-Asistant/infra/docker/Dockerfile.backend)
- [infra/docker/docker-compose.yml](/e:/My%20project%20with%20git/AI-Asistant/infra/docker/docker-compose.yml)

## Recommended Next Build Steps

1. Replace the rule-based reasoner with a cloud LLM adapter that enforces JSON schema output.
2. Move heavy plugins to async worker jobs backed by Redis.
3. Switch from demo API key auth to JWT plus workspace membership checks from the database.
4. Add per-workspace file encryption and retention rules.
5. Add plugin-level approval policies for sensitive actions like outbound email or external search.
