from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import ApiPrincipal, require_api_principal
from app.schemas.system import LLMConfigurationResponse, LLMSelectionRequest, LLMStatusResponse
from app.services.llm_gateway import LLMGateway


router = APIRouter()
gateway = LLMGateway()


@router.get("/status")
def system_status() -> dict[str, object]:
    return {
        "status": "ok",
        "llm": gateway.status(),
    }


@router.get("/llm", response_model=LLMConfigurationResponse)
def llm_configuration(
    _principal: ApiPrincipal = Depends(require_api_principal),
) -> LLMConfigurationResponse:
    status = gateway.status()
    return LLMConfigurationResponse(
        provider=status["provider"],
        model=status["model"],
        enable_cloud_reasoner=status["state"] != "disabled",
        status=LLMStatusResponse(**status),
    )


@router.post("/llm", response_model=LLMConfigurationResponse)
def update_llm_configuration(
    payload: LLMSelectionRequest,
    _principal: ApiPrincipal = Depends(require_api_principal),
) -> LLMConfigurationResponse:
    try:
        data = gateway.configure(
            provider=payload.provider,
            model=payload.model,
            enable_cloud_reasoner=payload.enable_cloud_reasoner,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return LLMConfigurationResponse(
        provider=str(data["provider"]),
        model=str(data["model"]),
        enable_cloud_reasoner=bool(data["enable_cloud_reasoner"]),
        status=LLMStatusResponse(**data["status"]),
    )


@router.post("/llm/check", response_model=LLMStatusResponse)
def check_llm_configuration(
    _principal: ApiPrincipal = Depends(require_api_principal),
) -> LLMStatusResponse:
    return LLMStatusResponse(**gateway.check())
