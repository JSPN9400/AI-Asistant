from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    workspace_id: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    workspace_id: str
    user_id: str
    role: str
