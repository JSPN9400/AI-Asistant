from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    user_input: str
    workspace_id: str
    context: dict[str, Any] | None = None
    attachments: list[str] = Field(default_factory=list)

    # Optional helpers for multi-step workflows
    confirmation: bool | None = None
    workflow_state: dict[str, Any] | None = None


class StructuredTask(BaseModel):
    task: str
    parameters: dict[str, Any]


class TaskResponse(BaseModel):
    task_id: str
    task: str
    parameters: dict[str, Any]
    result: dict[str, Any]


class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    content_type: str


class TaskHistoryItem(BaseModel):
    task_id: str
    workspace_id: str
    user_id: str
    task: str
    status: str
    input_text: str
    output_text: str
    created_at: str
