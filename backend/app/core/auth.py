from dataclasses import dataclass
from typing import Optional

from fastapi import Header, HTTPException

from app.config import settings
from app.core.security import verify_access_token


@dataclass
class ApiPrincipal:
    user_id: str
    workspace_id: str
    role: str


def require_api_principal(
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
    x_user_id: str = Header(default="demo-user"),
    x_workspace_id: str = Header(default="demo-workspace"),
    x_role: str = Header(default="employee"),
) -> ApiPrincipal:
    if authorization and authorization.lower().startswith("bearer "):
        payload = verify_access_token(authorization.split(" ", 1)[1])
        return ApiPrincipal(
            user_id=str(payload["user_id"]),
            workspace_id=str(payload["workspace_id"]),
            role=str(payload.get("role", "employee")),
        )

    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return ApiPrincipal(user_id=x_user_id, workspace_id=x_workspace_id, role=x_role)
