from __future__ import annotations

from app.plugins.base import BasePlugin, PluginContext
from app.services.llm_gateway import LLMGateway


GENERAL_ASSISTANT_PROMPT = """
You are Sikha, a practical AI assistant for normal users.
Answer the user's question directly and clearly.
- Give the best useful answer you can
- Be concise but natural
- If the question asks for recent live facts and you do not have verified live retrieval, say that clearly
- If you are unsure, state uncertainty instead of inventing facts
"""


class GeneralAssistantPlugin(BasePlugin):
    name = "general_assistant"
    description = "Answers normal user questions and open-ended requests through the LLM."
    supported_actions = ["answer_question", "general_help"]
    input_fields = ["prompt"]
    output_fields = ["message"]

    def __init__(self) -> None:
        self.gateway = LLMGateway()

    def execute(self, parameters: dict, context: PluginContext) -> dict:
        prompt = str(parameters.get("prompt", "")).strip()
        if not prompt:
            prompt = str(context.get("original_user_input", "")).strip()
        if not prompt:
            return {
                "status": "error",
                "message": "I need a question or request to answer.",
            }

        if self.gateway.is_configured():
            try:
                # Route to the best provider for general chat.
                answer = self.gateway.complete_text_for_task("general_assistant", GENERAL_ASSISTANT_PROMPT, prompt).strip()
                if answer:
                    return {
                        "status": "success",
                        "message": answer,
                    }
            except Exception as exc:
                return {
                    "status": "error",
                    "message": self._friendly_llm_error(str(exc)),
                }

        return {
            "status": "success",
            "message": (
                "General question answering needs the cloud LLM to be enabled. "
                "Set ASSISTANT_ENABLE_CLOUD_REASONER=true and configure OPENAI_API_KEY, "
                "GEMINI_API_KEY, or Ollama."
            ),
        }

    @staticmethod
    def _friendly_llm_error(message: str) -> str:
        lowered = message.lower()
        if "quota" in lowered or "resource_exhausted" in lowered or '"code": 429' in lowered:
            return (
                "The cloud model is configured, but its quota is exhausted right now. "
                "Try again later, switch to another provider, or use OPENAI_API_KEY with ASSISTANT_LLM_PROVIDER=openai."
            )
        if "api key" in lowered or "unauthorized" in lowered or "permission" in lowered:
            return "The cloud model is configured incorrectly. Check the API key and provider settings."
        return "I could not reach the cloud model right now. Check the selected provider and try again."
