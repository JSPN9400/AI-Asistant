from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.core.task_planner import plan as plan_task
from app.core.workspace import ensure_workspace_access
from app.db.models import TaskRun
from app.db.repositories.task_runs import TaskRunRepository
from app.db.session import init_db
from app.schemas.task import StructuredTask
from app.services.audit_service import AuditService
from app.services.llm_reasoner import LLMReasoner
from app.services.plugin_manager import PluginManager
from app.services.response_composer import ResponseComposer


# Intents (task names) that should always prompt for confirmation before executing.
DANGEROUS_TASKS = {"email_writer", "delete_file", "install_program"}


class TaskRouter:
    def __init__(self) -> None:
        init_db()
        self.reasoner = LLMReasoner()
        self.plugin_manager = PluginManager()
        self.response_composer = ResponseComposer()
        self.audit = AuditService()
        self.task_runs = TaskRunRepository()

    def handle(
        self,
        user_input: str,
        context: dict,
        confirmation: bool | None = None,
        workflow_state: dict[str, Any] | None = None,
    ) -> dict:
        requested_workspace = context["workspace_id"]
        principal_workspace = context.get("principal_workspace_id", requested_workspace)
        ensure_workspace_access(requested_workspace, principal_workspace)

        if workflow_state:
            workflow = workflow_state.get("workflow", [])
            current_step = int(workflow_state.get("current_step", 0))
        else:
            structured_task = self.reasoner.reason(user_input)
            plan = plan_task(user_input, structured_task)
            if plan and plan.get("workflow"):
                workflow = plan["workflow"]
                current_step = 0
            else:
                # Single-step execution (legacy behavior)
                return self._execute_single_task(user_input, structured_task, context)

        if not workflow:
            # No workflow defined: fallback to single-step rerun (e.g., empty workflow_state)
            structured_task = self.reasoner.reason(user_input)
            return self._execute_single_task(user_input, structured_task, context)

        # Execute remaining workflow steps sequentially.
        assistant_replies: List[str] = []
        for idx in range(current_step, len(workflow)):
            step = workflow[idx]
            intent = step.get("intent")
            params = step.get("parameters", {}) or {}
            requires_confirmation = bool(step.get("requires_confirmation", False))

            if requires_confirmation or intent in DANGEROUS_TASKS:
                if not confirmation:
                    return self._pause_for_confirmation(
                        user_input=user_input,
                        context=context,
                        workflow=workflow,
                        current_step=idx,
                        intent=intent,
                        parameters=params,
                    )

            result, assistant_reply = self._execute_step(intent, params, context, user_input)
            assistant_replies.append(assistant_reply)

            if result.get("status") != "success":
                # stop on failure
                return self._build_response(
                    task=intent,
                    parameters=params,
                    result=result,
                    assistant_reply="\n".join(assistant_replies),
                )

        # Completed workflow.
        combined_reply = "\n".join(assistant_replies).strip()
        return self._build_response(
            task=workflow[-1].get("intent", "workflow"),
            parameters=workflow[-1].get("parameters", {}),
            result={"status": "success"},
            assistant_reply=combined_reply,
            user_input=user_input,
            context=context,
        )

    def _pause_for_confirmation(
        self,
        user_input: str,
        context: dict,
        workflow: List[Dict[str, Any]],
        current_step: int,
        intent: str,
        parameters: dict,
    ) -> dict:
        prompt = (
            f"This workflow includes a sensitive action ({intent}). "
            "Please confirm by resubmitting the request with `confirmation=true`."
        )
        return self._build_response(
            task="workflow",
            parameters={},
            result={
                "status": "requires_confirmation",
                "assistant_reply": prompt,
                "pending_workflow": {
                    "workflow": workflow,
                    "current_step": current_step,
                },
            },
            user_input=user_input,
            context=context,
        )

    def _execute_single_task(
        self, user_input: str, structured_task: StructuredTask, context: dict
    ) -> dict:
        task_name = structured_task.task
        result, assistant_reply = self._execute_step(
            task_name, structured_task.parameters, context, user_input
        )
        return self._build_response(
            task=task_name,
            parameters=structured_task.parameters,
            result=result,
            assistant_reply=assistant_reply,
            user_input=user_input,
            context=context,
        )

    def _execute_step(
        self,
        task_name: str,
        parameters: dict,
        context: dict,
        user_input: str,
    ) -> tuple[dict, str]:
        plugin = self.plugin_manager.get_plugin(task_name)
        plugin_context = {
            **context,
            "original_user_input": user_input,
        }
        result = plugin.execute(parameters, plugin_context)
        structured_task = StructuredTask(task=task_name, parameters=parameters)
        assistant_reply = self.response_composer.compose(
            user_input=user_input,
            structured_task=structured_task.model_dump(),
            result=result,
        )
        return result, assistant_reply

    def _build_response(
        self,
        task: str,
        parameters: dict,
        result: dict,
        assistant_reply: str,
        user_input: str,
        context: dict,
    ) -> dict:
        self.audit.log_task(
            workspace_id=context["workspace_id"],
            user_id=context["user_id"],
            task_name=task,
        )
        task_run = self.task_runs.create(
            TaskRun(
                workspace_id=context["workspace_id"],
                user_id=context["user_id"],
                task_name=task,
                status=result.get("status", "success"),
                input_text=user_input,
                output_text=json.dumps(
                    {
                        **result,
                        "assistant_reply": assistant_reply,
                    }
                ),
            )
        )

        return {
            "task": task,
            "parameters": parameters,
            "result": {
                **result,
                "assistant_reply": assistant_reply,
                "task_run_id": task_run.id,
            },
        }
