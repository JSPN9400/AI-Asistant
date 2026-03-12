from dotenv import load_dotenv
from importlib import import_module
import os
import sys
from typing import TYPE_CHECKING

from assistant.router import execute_intent
from brain.nlu import NLU
from memory.sqlite_store import SQLiteMemory

if TYPE_CHECKING:
    from voice.speech_to_text import SpeechToText
    from voice.text_to_speech import TextToSpeech


EXIT_KEYWORDS = {"exit", "quit", "stop", "goodbye"}
ASSISTANT_NAME = "Sikha"
END_OF_INPUT = object()


def _voice_input_enabled() -> bool:
    if os.getenv("ASSISTANT_TEXT_MODE", "").strip().lower() in {"1", "true", "yes", "on"}:
        return False
    return sys.stdin.isatty()


def _create_speech_to_text() -> "SpeechToText | None":
    if not _voice_input_enabled():
        return None
    try:
        speech_module = import_module("voice.speech_to_text")
        return speech_module.SpeechToText()
    except Exception as exc:
        print(f"Voice input disabled: {exc}")
        return None


def _create_text_to_speech() -> "TextToSpeech | None":
    try:
        speech_module = import_module("voice.text_to_speech")
        return speech_module.TextToSpeech()
    except Exception as exc:
        print(f"Voice output disabled: {exc}")
        return None


def _speak(tts: "TextToSpeech | None", message: str) -> None:
    if tts is None:
        print(f"{ASSISTANT_NAME}: {message}")
        return
    tts.speak(message)


def _get_user_input(stt: "SpeechToText | None") -> str | None | object:
    if stt is not None:
        return stt.listen()

    try:
        text = input("You: ").strip()
    except EOFError:
        return END_OF_INPUT
    return text or None


def main() -> None:
    load_dotenv()

    stt = _create_speech_to_text()
    tts = _create_text_to_speech()
    nlu = NLU()
    memory = SQLiteMemory()

    if stt is None:
        _speak(
            tts,
            f"Hello, I am {ASSISTANT_NAME}. Voice input is unavailable, so type your commands."
        )
    else:
        _speak(tts, f"Hello, I am {ASSISTANT_NAME}. How can I help you?")

    while True:
        text = _get_user_input(stt)
        if text is END_OF_INPUT:
            _speak(tts, "Okay, goodbye.")
            break
        if not text:
            _speak(tts, "I didn't catch that. Please repeat.")
            continue

        if any(k in text.lower() for k in EXIT_KEYWORDS):
            _speak(tts, "Okay, goodbye.")
            break

        try:
            parsed = nlu.parse(text)
        except Exception as exc:
            _speak(tts, f"I could not process that request right now: {exc}")
            continue

        memory.log_command(parsed.raw_text, parsed.intent)

        result = execute_intent(parsed.intent, parsed.slots)
        nlu.learn_from_result(parsed, result.success)
        _speak(tts, result.message)


if __name__ == "__main__":
    main()

