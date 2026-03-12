from __future__ import annotations

from sqlmodel import select

from app.db.models import UploadedFile
from app.db.session import get_session


class UploadedFileRepository:
    def create(self, uploaded_file: UploadedFile) -> UploadedFile:
        with get_session() as session:
            session.add(uploaded_file)
            session.commit()
            session.refresh(uploaded_file)
            return uploaded_file

    def get_by_id(self, file_id: str, workspace_id: str) -> UploadedFile | None:
        with get_session() as session:
            statement = select(UploadedFile).where(
                UploadedFile.id == file_id,
                UploadedFile.workspace_id == workspace_id,
            )
            return session.exec(statement).first()
