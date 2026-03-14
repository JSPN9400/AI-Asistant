from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_auth import router as auth_router
from app.api.routes_files import router as files_router
from app.api.routes_plugins import router as plugins_router
from app.api.routes_system import router as system_router
from app.api.routes_tasks import router as tasks_router
from app.core.logging import configure_logging
from app.db.session import init_db


configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Sikha Work Assistant API",
    version="0.1.0",
    description="Cloud-first AI productivity backend for low-spec workplace devices.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(system_router, prefix="/system", tags=["system"])
app.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
app.include_router(plugins_router, prefix="/plugins", tags=["plugins"])
app.include_router(files_router, prefix="/files", tags=["files"])


@app.get("/health", include_in_schema=False)
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


frontend_dir = Path(__file__).resolve().parents[2] / "frontend" / "web" / "app"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
