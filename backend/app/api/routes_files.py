from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.auth import ApiPrincipal, require_api_principal
from app.core.workspace import WorkspaceAccessError, ensure_workspace_access
from app.schemas.task import FileUploadResponse
from app.services.file_service import FileService


router = APIRouter()
file_service = FileService()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    workspace_id: str,
    file: UploadFile = File(...),
    principal: ApiPrincipal = Depends(require_api_principal),
) -> FileUploadResponse:
    try:
        ensure_workspace_access(workspace_id, principal.workspace_id)
    except WorkspaceAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    stored = await file_service.save_upload(
        workspace_id=workspace_id,
        uploaded_by=principal.user_id,
        upload=file,
    )
    return FileUploadResponse(
        file_id=stored["file_id"],
        filename=stored["filename"],
        content_type=stored["content_type"],
    )
