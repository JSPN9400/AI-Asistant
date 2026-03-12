from __future__ import annotations

from app.plugins.base import BasePlugin, PluginContext


class DesktopControlPlugin(BasePlugin):
    name = "desktop_control"
    description = "Handles desktop-style commands that are unsupported in the browser client."
    supported_actions = ["open_app", "close_app", "screenshot", "system_message"]
    input_fields = ["action", "target"]
    output_fields = ["message"]

    def execute(self, parameters: dict, context: PluginContext) -> dict:
        action = parameters.get("action", "system_message")
        target = parameters.get("target", "that action")

        if action == "open_app":
            message = (
                f"I understood you want to open {target}, but this web version cannot open apps on your computer. "
                "Use the desktop agent for local app control, or ask me to open a website instead."
            )
        elif action == "close_app":
            message = (
                f"I understood you want to close {target}, but browser mode cannot control local processes. "
                "Use the desktop agent for system actions."
            )
        elif action == "screenshot":
            message = (
                "I understood you want a screenshot, but browser mode cannot capture your full desktop. "
                "Use the desktop agent for screenshots."
            )
        else:
            message = "This command needs desktop-agent access rather than the browser app."

        return {
            "status": "success",
            "message": message,
            "action": action,
            "target": target,
        }
