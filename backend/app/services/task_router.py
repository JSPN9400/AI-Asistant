from __future__ import annotations

import json

from app.core.workspace import ensure_workspace_access
from app.db.models import TaskRun
from app.db.repositories.task_runs import TaskRunRepository
from app.db.session import init_db
from app.services.audit_service import AuditService
from app.services.llm_reasoner import LLMReasoner
from app.services.plugin_manager import PluginManager


class TaskRouter:
    def __init__(self) -> None:
        init_db()
        self.reasoner = LLMReasoner()
        self.plugin_manager = PluginManager()
        self.audit = AuditService()
        self.task_runs = TaskRunRepository()

    def handle(self, user_input: str, context: dict) -> dict:
        requested_workspace = context["workspace_id"]
        principal_workspace = context.get("principal_workspace_id", requested_workspace)
        ensure_workspace_access(requested_workspace, principal_workspace)

        structured_task = self.reasoner.reason(user_input)
        plugin = self.plugin_manager.get_plugin(structured_task.task)
        result = plugin.execute(structured_task.parameters, context)

        self.audit.log_task(
            workspace_id=context["workspace_id"],
            user_id=context["user_id"],
            task_name=structured_task.task,
        )
        task_run = self.task_runs.create(
            TaskRun(
                workspace_id=context["workspace_id"],
                user_id=context["user_id"],
                task_name=structured_task.task,
                status=result.get("status", "success"),
                input_text=user_input,
                output_text=json.dumps(result),
            )
        )

        return {
            "task": structured_task.task,
            "parameters": structured_task.parameters,
            "result": {
                **result,
                "task_run_id": task_run.id,
            },
        }
