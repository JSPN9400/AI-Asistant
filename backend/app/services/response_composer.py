from __future__ import annotations

from app.services.llm_gateway import LLMGateway


REPLY_SYSTEM_PROMPT = """
You are Sikha, a practical AI work assistant for office staff, sales teams, FMCG teams, and operations users.
Write a short, natural assistant reply that:
- directly answers the user's request
- explains the action taken or limitation clearly
- sounds helpful and professional
- stays under 80 words
- avoids JSON
"""


class ResponseComposer:
    def __init__(self) -> None:
        self.gateway = LLMGateway()

    def compose(self, user_input: str, structured_task: dict, result: dict) -> str:
        direct_reply = self._direct_reply(result)
        if direct_reply:
            return direct_reply

        if self.gateway.is_configured():
            try:
                prompt = (
                    f"User input: {user_input}\n"
                    f"Structured task: {structured_task}\n"
                    f"Execution result: {result}\n"
                    "Respond as the assistant to the user."
                )
                # Use task-aware routing for reply polishing.
                task_name = structured_task.get("task", "general_assistant")
                response = self.gateway.complete_text_for_task(task_name, REPLY_SYSTEM_PROMPT, prompt).strip()
                if response:
                    return response
            except Exception:
                pass

        return self._fallback_reply(structured_task.get("task", ""), result)

    @staticmethod
    def _direct_reply(result: dict) -> str:
        for key in ("assistant_reply", "message"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    @staticmethod
    def _fallback_reply(task: str, result: dict) -> str:
        if result.get("message"):
            return str(result["message"])
        if result.get("report"):
            return "I created the report and highlighted the main actions for you."
        if result.get("summary"):
            return "I summarized the notes and extracted the main action items."
        if result.get("insights"):
            return "I analyzed the data and pulled out the most useful insights."
        return f"I completed the {task or 'requested'} task."
