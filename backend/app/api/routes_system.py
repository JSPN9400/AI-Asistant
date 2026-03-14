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
        enable_auto_routing=bool(getattr(settings, "enable_auto_llm_routing", True)),
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

    # Update auto-routing flag separately so the gateway can choose providers per task.
    from app.config import settings as _settings

    _settings.enable_auto_llm_routing = payload.enable_auto_routing

    return LLMConfigurationResponse(
        provider=str(data["provider"]),
        model=str(data["model"]),
        enable_cloud_reasoner=bool(data["enable_cloud_reasoner"]),
        enable_auto_routing=bool(_settings.enable_auto_llm_routing),
        status=LLMStatusResponse(**data["status"]),
    )


@router.post("/llm/check", response_model=LLMStatusResponse)
def check_llm_configuration(
    _principal: ApiPrincipal = Depends(require_api_principal),
) -> LLMStatusResponse:
    return LLMStatusResponse(**gateway.check())
