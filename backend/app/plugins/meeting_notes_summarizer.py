from __future__ import annotations

from app.plugins.base import BasePlugin, PluginContext
from app.services.file_service import FileService
from app.services.llm_gateway import LLMGateway


MEETING_SUMMARY_PROMPT = """
You are Sikha, a concise workplace assistant.
Summarize the provided notes for an office worker.
Return plain text with:
1. A short summary paragraph
2. Action items as lines starting with "-"
Keep it practical and brief.
"""


class MeetingNotesSummarizerPlugin(BasePlugin):
    name = "meeting_notes_summarizer"
    description = "Turns raw meeting notes into concise action-oriented summaries."
    supported_actions = ["summarize_meeting", "extract_action_items"]
    input_fields = ["source", "style", "meeting_type"]
    output_fields = ["summary", "action_items"]
    requires_files = True

    def __init__(self) -> None:
        self.files = FileService()
        self.gateway = LLMGateway()

    def execute(self, parameters: dict, context: PluginContext) -> dict:
        attachments = context.get("attachments", [])
        workspace_id = context.get("workspace_id", "")
        attachment_text = None
        attachment_preview = None
        if attachments:
            attachment_text = self.files.load_attachment_text(workspace_id, attachments[0])
            attachment_preview = self.files.load_attachment_preview(workspace_id, attachments[0])

        if attachment_text and attachment_text.get("text"):
            summary, action_items = self._summarize_text(attachment_text["text"])
            if summary or action_items:
                return {
                    "status": "success",
                    "summary": summary or ["Summary generated from uploaded file."],
                    "action_items": action_items or ["Review uploaded notes and confirm next steps."],
                    "style": parameters.get("style", "bullet_summary"),
                    "source_preview": attachment_preview,
                }

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

    def _summarize_text(self, text: str) -> tuple[list[str], list[str]]:
        if self.gateway.is_configured():
            try:
                response = self.gateway.complete_text(MEETING_SUMMARY_PROMPT, text).strip()
                summary_lines, action_items = self._parse_summary_response(response)
                if summary_lines or action_items:
                    return summary_lines, action_items
            except Exception:
                pass

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        summary_lines = lines[:3]
        action_items = []
        for line in lines:
            lowered = line.lower()
            if any(marker in lowered for marker in ("action", "follow up", "next step", "owner", "due")):
                action_items.append(line)
            if len(action_items) == 3:
                break
        return summary_lines, action_items

    @staticmethod
    def _parse_summary_response(response: str) -> tuple[list[str], list[str]]:
        lines = [line.strip() for line in response.splitlines() if line.strip()]
        summary_lines = []
        action_items = []
        for line in lines:
            if line.startswith("-"):
                action_items.append(line.removeprefix("-").strip())
            else:
                summary_lines.append(line)
        return summary_lines[:4], action_items[:5]
