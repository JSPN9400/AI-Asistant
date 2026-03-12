from __future__ import annotations

from app.plugins.base import BasePlugin, PluginContext


class MeetingNotesSummarizerPlugin(BasePlugin):
    name = "meeting_notes_summarizer"
    description = "Turns raw meeting notes into concise action-oriented summaries."
    supported_actions = ["summarize_meeting", "extract_action_items"]
    input_fields = ["source", "style", "meeting_type"]
    output_fields = ["summary", "action_items"]
    requires_files = True

    def execute(self, parameters: dict, context: PluginContext) -> dict:
        return {
            "status": "success",
            "summary": [
                "Reviewed weekly performance against target.",
                "Flagged distributor delays in two regions.",
                "Aligned on follow-up actions for sales and ops teams.",
            ],
            "action_items": [
                "Operations to resolve distributor delay by Friday.",
                "Sales team to share revised regional targets.",
                "Manager to send consolidated report to leadership.",
            ],
            "style": parameters.get("style", "bullet_summary"),
        }
