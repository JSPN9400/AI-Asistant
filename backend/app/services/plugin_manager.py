from __future__ import annotations

import importlib
import inspect
import pkgutil

from app import plugins as plugins_package
from app.plugins.base import BasePlugin


class PluginManager:
    def __init__(self) -> None:
        self._plugins = self._discover_plugins()

    def _discover_plugins(self) -> dict[str, BasePlugin]:
        discovered: dict[str, BasePlugin] = {}

        for module_info in pkgutil.iter_modules(plugins_package.__path__):
            if module_info.name.startswith("_") or module_info.name == "base":
                continue

            module = importlib.import_module(f"{plugins_package.__name__}.{module_info.name}")
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(cls, BasePlugin)
                    and cls is not BasePlugin
                    and not inspect.isabstract(cls)
                    and cls.__module__.startswith(f"{plugins_package.__name__}.")
                ):
                    plugin = cls()
                    discovered[plugin.name] = plugin

        return discovered

    def get_plugin(self, name: str) -> BasePlugin:
        if name not in self._plugins:
            raise ValueError(f"Unknown plugin: {name}")
        return self._plugins[name]

    def list_plugins(self) -> list[BasePlugin]:
        return list(self._plugins.values())
