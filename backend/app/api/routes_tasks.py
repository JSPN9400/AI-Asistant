from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import ApiPrincipal, require_api_principal
from app.core.workspace import WorkspaceAccessError
from app.db.repositories.task_runs import TaskRunRepository
from app.schemas.task import TaskHistoryItem, TaskRequest, TaskResponse
from app.services.task_router import TaskRouter


router = APIRouter()
task_router = TaskRouter()
task_run_repository = TaskRunRepository()


@router.post("/", response_model=TaskResponse)
def run_task(
    payload: TaskRequest,
    principal: ApiPrincipal = Depends(require_api_principal),
) -> TaskResponse:
    try:
        result = task_router.handle(
            user_input=payload.user_input,
            context={
                "workspace_id": payload.workspace_id,
                "principal_workspace_id": principal.workspace_id,
                "user_id": principal.user_id,
                "role": principal.role,
                "attachments": payload.attachments,
                "context": payload.context or {},
            },
        )
    except WorkspaceAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return TaskResponse(
        task_id=result["result"].get("task_run_id", ""),
        task=result["task"],
        parameters=result["parameters"],
        result=result["result"],
    )


@router.get("/history", response_model=list[TaskHistoryItem])
def task_history(
    workspace_id: str,
    limit: int = 20,
    principal: ApiPrincipal = Depends(require_api_principal),
) -> list[TaskHistoryItem]:
    try:
        from app.core.workspace import ensure_workspace_access

        ensure_workspace_access(workspace_id, principal.workspace_id)
    except WorkspaceAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    history = task_run_repository.list_recent(workspace_id=workspace_id, limit=limit)
    return [
        TaskHistoryItem(
            task_id=item.id,
            workspace_id=item.workspace_id,
            user_id=item.user_id,
            task=item.task_name,
            status=item.status,
            input_text=item.input_text,
            output_text=item.output_text,
            created_at=item.created_at.isoformat(),
        )
        for item in history
    ]
