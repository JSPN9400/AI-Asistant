from __future__ import annotations

from sqlmodel import select

from app.db.models import TaskRun
from app.db.session import get_session


class TaskRunRepository:
    def create(self, task_run: TaskRun) -> TaskRun:
        with get_session() as session:
            session.add(task_run)
            session.commit()
            session.refresh(task_run)
            return task_run

    def list_recent(self, workspace_id: str, limit: int = 20) -> list[TaskRun]:
        with get_session() as session:
            statement = (
                select(TaskRun)
                .where(TaskRun.workspace_id == workspace_id)
                .order_by(TaskRun.created_at.desc())
                .limit(limit)
            )
            return list(session.exec(statement))
