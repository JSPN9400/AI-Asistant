from __future__ import annotations

from sqlalchemy import inspect, text

from app.db.models import UploadedFile
from app.db.session import engine


class UploadedFileRepository:
    def create(self, uploaded_file: UploadedFile) -> UploadedFile:
        columns = self._uploaded_file_columns()
        values = {
            "id": uploaded_file.id,
            "workspace_id": uploaded_file.workspace_id,
            "uploaded_by": uploaded_file.uploaded_by,
            "filename": uploaded_file.filename,
            "storage_path": uploaded_file.storage_path,
            "created_at": uploaded_file.created_at,
        }
        if "content_type" in columns:
            values["content_type"] = uploaded_file.content_type

        ordered_columns = list(values.keys())
        placeholders = ", ".join(f":{column}" for column in ordered_columns)
        sql = (
            f"INSERT INTO uploadedfile ({', '.join(ordered_columns)}) "
            f"VALUES ({placeholders})"
        )
        with engine.begin() as connection:
            connection.execute(text(sql), values)
        return uploaded_file

    def get_by_id(self, file_id: str, workspace_id: str) -> UploadedFile | None:
        columns = self._uploaded_file_columns()
        selected_columns = [
            "id",
            "workspace_id",
            "uploaded_by",
            "filename",
            "storage_path",
            "created_at",
        ]
        if "content_type" in columns:
            selected_columns.append("content_type")

        sql = (
            f"SELECT {', '.join(selected_columns)} FROM uploadedfile "
            "WHERE id = :file_id AND workspace_id = :workspace_id"
        )
        with engine.begin() as connection:
            row = connection.execute(
                text(sql),
                {"file_id": file_id, "workspace_id": workspace_id},
            ).mappings().first()

        if row is None:
            return None

        payload = dict(row)
        payload.setdefault("content_type", "application/octet-stream")
        return UploadedFile(**payload)

    @staticmethod
    def _uploaded_file_columns() -> set[str]:
        inspector = inspect(engine)
        if "uploadedfile" not in inspector.get_table_names():
            return set()
        return {column["name"] for column in inspector.get_columns("uploadedfile")}
