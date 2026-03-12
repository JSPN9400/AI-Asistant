from pydantic import BaseModel


class PluginDescriptor(BaseModel):
    name: str
    description: str
    supported_actions: list[str]
    input_fields: list[str] = []
    output_fields: list[str] = []
    requires_files: bool = False
