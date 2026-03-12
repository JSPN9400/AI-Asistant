from assistant.runtime import SikhaRuntime


END_OF_INPUT = object()


def _read_typed_input(prompt: str = "You: ") -> str | None | object:
    try:
        text = input(prompt).strip()
    except EOFError:
        return END_OF_INPUT
    return text or None


def main() -> None:
    assistant = SikhaRuntime()
    assistant.speak(assistant.greeting())

    while True:
        text = assistant.listen_for_voice()
        if not text:
            typed = _read_typed_input(
                "You: " if not assistant.voice_available else "Voice not detected. Type a command, or press Enter to try voice again.\nYou: "
            )
            if typed is END_OF_INPUT:
                assistant.speak("Okay, goodbye.")
                break
            text = typed

        result = assistant.process_text(text or "")
        assistant.speak(result.response)
        if result.exit_requested:
            break


if __name__ == "__main__":
    main()
