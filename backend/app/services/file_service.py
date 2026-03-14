from __future__ import annotations

import csv
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import settings
from app.db.models import UploadedFile
from app.db.repositories.files import UploadedFileRepository


class FileService:
    def __init__(self) -> None:
        self.root = Path(settings.file_storage_path)
        self.root.mkdir(parents=True, exist_ok=True)
        self.repository = UploadedFileRepository()

    async def save_upload(self, workspace_id: str, uploaded_by: str, upload: UploadFile) -> dict[str, str]:
        workspace_dir = self.root / workspace_id
        workspace_dir.mkdir(parents=True, exist_ok=True)

        file_id = uuid4().hex
        filename = Path(upload.filename or f"{file_id}.bin").name or f"{file_id}.bin"
        target = workspace_dir / f"{file_id}-{filename}"
        content = await upload.read()
        target.write_bytes(content)
        stored = self.repository.create(
            UploadedFile(
                id=file_id,
                workspace_id=workspace_id,
                uploaded_by=uploaded_by,
                filename=filename,
                storage_path=str(target),
                content_type=upload.content_type or "application/octet-stream",
            )
        )

        return {
            "file_id": stored.id,
            "filename": stored.filename,
            "content_type": stored.content_type,
            "uploaded_by": stored.uploaded_by,
            "path": stored.storage_path,
        }

    def load_attachment_preview(self, workspace_id: str, file_id: str) -> dict[str, object] | None:
        uploaded_file = self.repository.get_by_id(file_id, workspace_id)
        if uploaded_file is None:
            return None

        path = Path(uploaded_file.storage_path)
        if not path.exists():
            return {
                "filename": uploaded_file.filename,
                "content_type": uploaded_file.content_type,
                "summary": "File record exists but storage path is missing.",
            }

        suffix = path.suffix.lower()
        if suffix in {".csv", ".tsv"}:
            delimiter = "\t" if suffix == ".tsv" else ","
            return self._summarize_delimited_file(path, uploaded_file.filename, delimiter)

        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return {
            "filename": uploaded_file.filename,
            "content_type": uploaded_file.content_type,
            "summary": f"{len(lines)} non-empty lines detected.",
            "sample": lines[:5],
        }

    def load_attachment_text(self, workspace_id: str, file_id: str, max_chars: int = 6000) -> dict[str, str] | None:
        uploaded_file = self.repository.get_by_id(file_id, workspace_id)
        if uploaded_file is None:
            return None

        path = Path(uploaded_file.storage_path)
        if not path.exists():
            return {
                "filename": uploaded_file.filename,
                "content_type": uploaded_file.content_type,
                "text": "",
            }

        suffix = path.suffix.lower()
        if suffix in {".csv", ".tsv"}:
            preview = self.load_attachment_preview(workspace_id, file_id) or {}
            lines = [",".join(preview.get("columns", []))]
            for row in preview.get("sample", []):
                lines.append(", ".join(str(item) for item in row))
            text = "\n".join(line for line in lines if line.strip())
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")

        cleaned = text.strip()
        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars].rstrip() + "\n...[truncated]"

        return {
            "filename": uploaded_file.filename,
            "content_type": uploaded_file.content_type,
            "text": cleaned,
        }

    def _summarize_delimited_file(self, path: Path, filename: str, delimiter: str) -> dict[str, object]:
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            reader = csv.reader(handle, delimiter=delimiter)
            rows = list(reader)

        if not rows:
            return {"filename": filename, "summary": "No rows found.", "sample": []}

        header = rows[0]
        data_rows = rows[1:] if len(rows) > 1 else []
        numeric_counts: dict[str, int] = {column: 0 for column in header}
        numeric_totals: dict[str, float] = {column: 0.0 for column in header}

        for row in data_rows:
            for index, column in enumerate(header):
                if index >= len(row):
                    continue
                try:
                    value = float(row[index])
                except ValueError:
                    continue
                numeric_counts[column] += 1
                numeric_totals[column] += value

        metrics = []
        for column in header:
            if numeric_counts[column]:
                metrics.append(
                    f"{column}: avg {numeric_totals[column] / numeric_counts[column]:.2f}"
                )

        return {
            "filename": filename,
            "summary": f"{len(data_rows)} data rows, {len(header)} columns.",
            "columns": header,
            "metrics": metrics[:5],
            "sample": data_rows[:3],
        }
