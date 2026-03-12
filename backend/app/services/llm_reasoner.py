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
- browser_navigator
- desktop_control
- general_assistant
- small_talk
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

        if text in {
            "hi",
            "hello",
            "hey",
            "hello sikha",
            "hi sikha",
            "hey sikha",
            "namaste",
            "namaste sikha",
            "sikha",
        }:
            return StructuredTask(
                task="small_talk",
                parameters={
                    "response": "Hello. I am ready. You can ask me to write reports, summarize notes, draft emails, analyze data, or open web tools.",
                },
            )

        if text.startswith(("open ", "go to ", "launch ", "khol", "kholo ", "open website ")):
            target = self._trim_prefix(
                user_input,
                "open website ",
                "open ",
                "go to ",
                "launch ",
                "kholo ",
                "khol do ",
                "khol ",
            )
            if target.lower() in {
                "chrome",
                "notepad",
                "calculator",
                "calc",
                "cmd",
                "command prompt",
                "explorer",
                "file explorer",
                "whatsapp",
                "telegram",
                "spotify",
                "vs code",
                "vscode",
            }:
                return StructuredTask(
                    task="desktop_control",
                    parameters={
                        "action": "open_app",
                        "target": target,
                    },
                )
            return StructuredTask(
                task="browser_navigator",
                parameters={
                    "action": "open_url",
                    "target": target,
                },
            )

        if text.startswith(("close ", "band karo ", "band kar do ")):
            target = self._trim_prefix(user_input, "close ", "band karo ", "band kar do ")
            return StructuredTask(
                task="desktop_control",
                parameters={
                    "action": "close_app",
                    "target": target,
                },
            )

        if any(phrase in text for phrase in {"screenshot", "take screenshot", "screen shot", "screenshot lo"}):
            return StructuredTask(
                task="desktop_control",
                parameters={
                    "action": "screenshot",
                    "target": "desktop",
                },
            )

        if "google" in text and ("search" in text or "find" in text or "dhundo" in text or "khojo" in text):
            query = self._trim_prefix(
                user_input,
                "search google for ",
                "google search ",
                "find on google ",
                "google pe search karo ",
                "google par search karo ",
                "search ",
            )
            if query == user_input:
                query = self._extract_search_subject(user_input, "google")
            return StructuredTask(
                task="browser_navigator",
                parameters={
                    "action": "google_search",
                    "query": query,
                },
            )

        if "youtube" in text and ("play" in text or "chalao" in text or "bajao" in text):
            query = (
                text.replace("play on youtube", "")
                .replace("play youtube", "")
                .replace("youtube pe", "")
                .replace("youtube par", "")
                .replace("chalao", "")
                .replace("bajao", "")
                .strip()
            )
            return StructuredTask(
                task="browser_navigator",
                parameters={
                    "action": "youtube_play",
                    "query": query or user_input,
                },
            )

        if "youtube" in text and ("search" in text or "find" in text or "dhundo" in text or "khojo" in text):
            query = (
                text.replace("search youtube for", "")
                .replace("youtube search", "")
                .replace("search on youtube", "")
                .replace("youtube pe search karo", "")
                .replace("youtube par search karo", "")
                .strip()
            )
            return StructuredTask(
                task="browser_navigator",
                parameters={
                    "action": "youtube_search",
                    "query": query or user_input,
                },
            )

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

        if any(phrase in text for phrase in {"write report", "make report", "generate report", "report banao"}):
            return StructuredTask(
                task="sales_report_generator",
                parameters={
                    "data_source": "uploaded_file",
                    "format": "professional_report",
                    "period": "weekly",
                    "audience": "manager",
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

        if any(phrase in text for phrase in {"summarize", "summary", "summarise", "notes summary"}):
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

        if any(phrase in text for phrase in {"draft", "reply to client", "write mail", "compose email"}):
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

        if any(phrase in text for phrase in {"analyze", "analyse", "data analysis", "check data"}):
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

        if any(phrase in text for phrase in {"what can you do", "help", "who are you"}):
            return StructuredTask(
                task="small_talk",
                parameters={
                    "response": "I can take workplace requests, draft emails, summarize meetings, analyze spreadsheets, run web searches, and open common sites.",
                },
            )

        if text.endswith("?") or text.startswith(
            (
                "who ",
                "what ",
                "when ",
                "where ",
                "why ",
                "how ",
                "which ",
                "can you ",
                "tell me ",
                "do you know ",
            )
        ):
            return StructuredTask(
                task="general_assistant",
                parameters={"prompt": user_input},
            )

        return StructuredTask(
            task="general_assistant",
            parameters={
                "prompt": user_input,
            },
        )

    @staticmethod
    def _trim_prefix(text: str, *prefixes: str) -> str:
        lowered = text.lower()
        for prefix in prefixes:
            if lowered.startswith(prefix):
                return text[len(prefix):].strip()
        return text.strip()

    @staticmethod
    def _extract_search_subject(text: str, engine: str) -> str:
        lowered = text.lower()
        marker = f"{engine} pe"
        if marker in lowered and "search karo" in lowered:
            start = lowered.find(marker) + len(marker)
            end = lowered.rfind("search karo")
            if end > start:
                return text[start:end].strip()
        marker = f"{engine} par"
        if marker in lowered and "search karo" in lowered:
            start = lowered.find(marker) + len(marker)
            end = lowered.rfind("search karo")
            if end > start:
                return text[start:end].strip()
        return text.strip()

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
