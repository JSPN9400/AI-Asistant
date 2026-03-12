from __future__ import annotations

from sqlmodel import select

from app.db.models import User, UserCredential, Workspace, WorkspaceMembership
from app.db.session import get_session


class AuthRepository:
    def get_user_by_email(self, email: str) -> User | None:
        with get_session() as session:
            statement = select(User).where(User.email == email)
            return session.exec(statement).first()

    def get_workspace(self, workspace_id: str) -> Workspace | None:
        with get_session() as session:
            statement = select(Workspace).where(Workspace.id == workspace_id)
            return session.exec(statement).first()

    def get_password_hash(self, user_id: str) -> str | None:
        with get_session() as session:
            statement = select(UserCredential).where(UserCredential.user_id == user_id)
            credential = session.exec(statement).first()
            return credential.password_hash if credential else None

    def get_membership(self, user_id: str, workspace_id: str) -> WorkspaceMembership | None:
        with get_session() as session:
            statement = select(WorkspaceMembership).where(
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.workspace_id == workspace_id,
            )
            return session.exec(statement).first()
