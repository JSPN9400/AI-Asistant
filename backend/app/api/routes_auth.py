from fastapi import APIRouter, HTTPException

from app.core.security import create_access_token, hash_text
from app.db.repositories.auth import AuthRepository
from app.schemas.auth import LoginRequest, LoginResponse


router = APIRouter()
auth_repository = AuthRepository()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    user = auth_repository.get_user_by_email(payload.email)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    password_hash = auth_repository.get_password_hash(user.id)
    if password_hash != hash_text(payload.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    membership = auth_repository.get_membership(user.id, payload.workspace_id)
    if membership is None:
        raise HTTPException(status_code=403, detail="User is not assigned to this workspace")

    access_token = create_access_token(
        {
            "user_id": user.id,
            "workspace_id": membership.workspace_id,
            "role": membership.role,
        }
    )
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        workspace_id=membership.workspace_id,
        user_id=user.id,
        role=membership.role,
    )
