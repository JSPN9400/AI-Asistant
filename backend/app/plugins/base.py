from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PluginContext(dict):
    pass


class BasePlugin(ABC):
    name: str
    description: str
    supported_actions: list[str]
    input_fields: list[str] = []
    output_fields: list[str] = []
    requires_files: bool = False

    @abstractmethod
    def execute(self, parameters: dict[str, Any], context: PluginContext) -> dict[str, Any]:
        raise NotImplementedError

    def descriptor(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "supported_actions": self.supported_actions,
            "input_fields": self.input_fields,
            "output_fields": self.output_fields,
            "requires_files": self.requires_files,
        }
