class WorkspaceAccessError(PermissionError):
    pass


def ensure_workspace_access(requested_workspace_id: str, principal_workspace_id: str) -> None:
    if requested_workspace_id != principal_workspace_id:
        raise WorkspaceAccessError("Workspace access denied")
