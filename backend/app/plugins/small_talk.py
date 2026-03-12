from __future__ import annotations

from app.plugins.base import BasePlugin, PluginContext


class SmallTalkPlugin(BasePlugin):
    name = "small_talk"
    description = "Handles greetings and general assistant replies."
    supported_actions = ["greet", "respond"]
    input_fields = ["response"]
    output_fields = ["message"]

    def execute(self, parameters: dict, context: PluginContext) -> dict:
        return {
            "status": "success",
            "message": parameters.get(
                "response",
                "I can help with reports, summaries, emails, data analysis, and web tasks.",
            ),
        }
