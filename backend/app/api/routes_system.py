from fastapi import APIRouter

from app.services.llm_gateway import LLMGateway


router = APIRouter()
gateway = LLMGateway()


@router.get("/status")
def system_status() -> dict[str, object]:
    return {
        "status": "ok",
        "llm": gateway.status(),
    }
