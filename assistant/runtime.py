from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
import os
import sys
from typing import TYPE_CHECKING

from dotenv import load_dotenv

from assistant.paths import env_file_candidates
from assistant.router import execute_intent
from brain.nlu import NLU
from memory.sqlite_store import SQLiteMemory

if TYPE_CHECKING:
    from brain.llm_client import LLMClient
    from voice.speech_to_text import SpeechToText
    from voice.text_to_speech import TextToSpeech


EXIT_KEYWORDS = {"exit", "quit", "stop", "goodbye"}
ASSISTANT_NAME = "Sikha"


@dataclass
class InteractionResult:
    success: bool
    response: str
    user_text: str
    intent: str | None = None
    exit_requested: bool = False


class SikhaRuntime:
    def __init__(
        self,
        *,
        enable_voice_input: bool | None = None,
        enable_voice_output: bool = True,
    ) -> None:
        self._load_environment()
        self.memory = SQLiteMemory()
        self.nlu = NLU(memory=self.memory)
        self.stt = self._create_speech_to_text(enable_voice_input)
        self.tts = self._create_text_to_speech() if enable_voice_output else None

    @property
    def voice_available(self) -> bool:
        return self.stt is not None

    def greeting(self) -> str:
        if self.stt is None:
            return f"Hello, I am {ASSISTANT_NAME}. Voice input is unavailable, so type your commands."
        return f"Hello, I am {ASSISTANT_NAME}. You can speak or type your commands."

    def listen_for_voice(self) -> str | None:
        if self.stt is None:
            return None
        return self.stt.listen()

    def speak(self, message: str) -> None:
        if self.tts is None:
            print(f"{ASSISTANT_NAME}: {message}")
            return
        self.tts.speak(message)

    def process_text(self, text: str) -> InteractionResult:
        cleaned = (text or "").strip()
        if not cleaned:
            return InteractionResult(
                success=False,
                response="I didn't catch that. Please repeat.",
                user_text="",
            )

        if any(keyword in cleaned.lower() for keyword in EXIT_KEYWORDS):
            return InteractionResult(
                success=True,
                response="Okay, goodbye.",
                user_text=cleaned,
                exit_requested=True,
            )

        try:
            parsed = self.nlu.parse(cleaned)
        except Exception as exc:
            return InteractionResult(
                success=False,
                response=f"I could not process that request right now: {exc}",
                user_text=cleaned,
            )

        try:
            self.memory.log_command(parsed.raw_text, parsed.intent)
        except Exception:
            # Keep the assistant responsive even if history logging fails.
            pass

        result = execute_intent(parsed.intent, parsed.slots)
        self.nlu.learn_from_result(parsed, result.success)
        return InteractionResult(
            success=result.success,
            response=result.message,
            user_text=cleaned,
            intent=parsed.intent,
        )

    def ask_model(self, prompt: str, system_prompt: str | None = None) -> str:
        cleaned = (prompt or "").strip()
        if not cleaned:
            return "Enter a prompt first."

        try:
            llm = self._get_llm()
            if llm is None:
                return "No model is configured. Set Gemini or Ollama/Phi-3 environment variables."
            return llm.complete_text(
                system_prompt or "You are Sikha, a concise and capable desktop AI assistant.",
                cleaned,
            )
        except Exception as exc:
            return f"Model request failed: {exc}"

    def llm_status(self) -> dict[str, str]:
        try:
            llm_module = import_module("brain.llm_client")
            return llm_module.get_llm_status()
        except Exception as exc:
            return {
                "provider": "unknown",
                "model": "",
                "available": "false",
                "message": str(exc),
            }

    def _get_llm(self) -> "LLMClient | None":
        try:
            return self.nlu._get_llm()
        except Exception:
            return None

    @staticmethod
    def _load_environment() -> None:
        for env_path in env_file_candidates():
            load_dotenv(dotenv_path=env_path, override=False)

    @staticmethod
    def _voice_input_default() -> bool:
        if os.getenv("ASSISTANT_TEXT_MODE", "").strip().lower() in {"1", "true", "yes", "on"}:
            return False
        return sys.stdin.isatty()

    def _create_speech_to_text(self, enable_voice_input: bool | None) -> "SpeechToText | None":
        voice_enabled = self._voice_input_default() if enable_voice_input is None else enable_voice_input
        if not voice_enabled:
            return None
        try:
            speech_module = import_module("voice.speech_to_text")
            return speech_module.SpeechToText()
        except Exception as exc:
            print(f"Voice input disabled: {exc}")
            return None

    @staticmethod
    def _create_text_to_speech() -> "TextToSpeech | None":
        try:
            speech_module = import_module("voice.text_to_speech")
            return speech_module.TextToSpeech()
        except Exception as exc:
            print(f"Voice output disabled: {exc}")
            return None
