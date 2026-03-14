from pydantic import BaseModel


class LLMSelectionRequest(BaseModel):
    provider: str
    model: str
    enable_cloud_reasoner: bool = True
    enable_auto_routing: bool = True


class LLMStatusResponse(BaseModel):
    provider: str
    model: str
    available: str
    state: str
    message: str
    checked_at: str | None = None


class LLMConfigurationResponse(BaseModel):
    provider: str
    model: str
    enable_cloud_reasoner: bool
    enable_auto_routing: bool
    status: LLMStatusResponse
