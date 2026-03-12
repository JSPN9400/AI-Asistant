from __future__ import annotations

import json
import re

from app.schemas.task import StructuredTask
from app.services.llm_gateway import LLMGateway


SYSTEM_PROMPT = """
Convert workplace requests into structured JSON.
Return only:
{
  "task": "<plugin_name>",
  "parameters": {...}
}

Available tasks:
- sales_report_generator
- meeting_notes_summarizer
- email_writer
- excel_data_analyzer
- web_search
"""


class LLMReasoner:
    """
    Uses a cloud LLM when configured and falls back to deterministic routing.
    """

    def __init__(self) -> None:
        self.gateway = LLMGateway()

    def reason(self, user_input: str) -> StructuredTask:
        if self.gateway.is_configured():
            try:
                payload = self.gateway.complete_json(SYSTEM_PROMPT, user_input)
                return self._parse_structured_task(payload)
            except Exception:
                pass

        return self._heuristic_reason(user_input)

    def _heuristic_reason(self, user_input: str) -> StructuredTask:
        text = user_input.lower().strip()

        if "sales report" in text or "weekly sales" in text:
            return StructuredTask(
                task="sales_report_generator",
                parameters={
                    "data_source": "uploaded_file",
                    "format": "professional_report",
                    "period": "weekly",
                    "audience": "sales_manager",
                },
            )

        if "meeting" in text or "summarize notes" in text or "meeting notes" in text:
            return StructuredTask(
                task="meeting_notes_summarizer",
                parameters={
                    "style": "bullet_summary",
                    "source": "uploaded_notes",
                },
            )

        if "email" in text or "mail" in text or "client response" in text:
            return StructuredTask(
                task="email_writer",
                parameters={
                    "tone": "professional",
                    "prompt": user_input,
                },
            )

        if "excel" in text or "analyze data" in text or "spreadsheet" in text:
            return StructuredTask(
                task="excel_data_analyzer",
                parameters={
                    "data_source": "uploaded_file",
                    "analysis_type": "summary",
                },
            )

        if "search" in text or "find on web" in text or "web search" in text:
            return StructuredTask(
                task="web_search",
                parameters={"query": user_input},
            )

        return StructuredTask(
            task="email_writer",
            parameters={
                "tone": "professional",
                "prompt": user_input,
            },
        )

    def _parse_structured_task(self, payload: str) -> StructuredTask:
        cleaned = payload.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise ValueError("Structured task payload must be a JSON object.")

        task = data.get("task")
        parameters = data.get("parameters", {})
        if not isinstance(task, str) or not task:
            raise ValueError("Structured task is missing 'task'.")
        if not isinstance(parameters, dict):
            raise ValueError("Structured task parameters must be an object.")

        return StructuredTask(task=task, parameters=parameters)
