from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class Organization(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Workspace(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    organization_id: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    email: str
    full_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserCredential(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WorkspaceMembership(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    workspace_id: str = Field(primary_key=True)
    role: str = "employee"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskRun(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    workspace_id: str
    user_id: str
    task_name: str
    status: str
    input_text: str
    output_text: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UploadedFile(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    workspace_id: str
    uploaded_by: str
    filename: str
    storage_path: str
    content_type: str = "application/octet-stream"
    created_at: datetime = Field(default_factory=datetime.utcnow)
