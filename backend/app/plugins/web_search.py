from __future__ import annotations

from app.plugins.base import BasePlugin, PluginContext


class WebSearchPlugin(BasePlugin):
    name = "web_search"
    description = "Handles web search tasks for operational questions."
    supported_actions = ["search_web"]
    input_fields = ["query", "region", "time_range"]
    output_fields = ["results"]

    def execute(self, parameters: dict, context: PluginContext) -> dict:
        return {
            "status": "success",
            "query": parameters.get("query", ""),
            "results": [
                "Market update summary placeholder",
                "Competitor pricing snapshot placeholder",
                "Industry news digest placeholder",
            ],
        }
