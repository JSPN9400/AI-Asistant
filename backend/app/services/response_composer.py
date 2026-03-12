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
        if self.gateway.is_configured():
            try:
                prompt = (
                    f"User input: {user_input}\n"
                    f"Structured task: {structured_task}\n"
                    f"Execution result: {result}\n"
                    "Respond as the assistant to the user."
                )
                response = self.gateway.complete_text(REPLY_SYSTEM_PROMPT, prompt).strip()
                if response:
                    return response
            except Exception:
                pass

        return self._fallback_reply(structured_task.get("task", ""), result)

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
