from fastapi import APIRouter, Depends

from app.core.auth import ApiPrincipal, require_api_principal
from app.schemas.plugin import PluginDescriptor
from app.services.plugin_manager import PluginManager


router = APIRouter()
plugin_manager = PluginManager()


@router.get("/", response_model=list[PluginDescriptor])
def list_plugins(
    _principal: ApiPrincipal = Depends(require_api_principal),
) -> list[PluginDescriptor]:
    return [PluginDescriptor(**plugin.descriptor()) for plugin in plugin_manager.list_plugins()]
