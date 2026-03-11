from typing import Any, Callable, Dict

from assistant.types import ActionResult
from actions import system_actions, web_actions, memory_actions, gmail_actions
from vision import vision_actions


Handler = Callable[[Dict[str, Any]], str]


INTENT_HANDLERS: Dict[str, Handler] = {
    "OPEN_APPLICATION": lambda slots: system_actions.open_application(
        slots.get("app_name", "")
    ),
    "CLOSE_APPLICATION": lambda slots: system_actions.close_application(
        slots.get("app_name", "")
    ),
    "OPEN_WEBSITE": lambda slots: system_actions.open_website(
        slots.get("url"), slots.get("query")
    ),
    "GOOGLE_SEARCH": lambda slots: web_actions.google_search(
        slots.get("query", "")
    ),
    "YOUTUBE_SEARCH": lambda slots: system_actions.youtube_search(
        slots.get("query", "")
    ),
    "YOUTUBE_PLAY": lambda slots: system_actions.youtube_play(
        slots.get("query", "")
    ),
    "TAKE_SCREENSHOT": lambda slots: system_actions.take_screenshot(),
    "CREATE_NOTE": lambda slots: memory_actions.create_note(
        slots.get("content", "")
    ),
    "LIST_NOTES": lambda slots: memory_actions.list_notes(
        slots.get("limit", 5)
    ),
    "CREATE_TASK": lambda slots: memory_actions.create_task(
        slots.get("description", "")
    ),
    "LIST_TASKS": lambda slots: memory_actions.list_tasks(
        slots.get("status"), slots.get("limit", 10)
    ),
    "COMPLETE_TASK": lambda slots: memory_actions.complete_task(
        int(slots.get("task_id", 0))
    ),
    "READ_EMAILS": lambda slots: gmail_actions.read_emails(
        slots.get("limit", 5)
    ),
    "SEND_EMAIL": lambda slots: gmail_actions.send_email(
        slots.get("to", ""),
        slots.get("subject", ""),
        slots.get("body", ""),
    ),
    "DESCRIBE_SCENE": lambda slots: vision_actions.describe_scene(),
}


def execute_intent(intent: str, slots: Dict[str, Any]) -> ActionResult:
    intent = intent.upper()
    handler = INTENT_HANDLERS.get(intent)

    if not handler:
        if intent == "SMALL_TALK":
            return ActionResult(True, slots.get("response", "Let's chat."))
        return ActionResult(
            False, f"I don't know how to handle intent '{intent}'."
        )

    try:
        message = handler(slots)
        return ActionResult(True, message)
    except Exception as exc:  # pragma: no cover - defensive
        return ActionResult(False, f"Error executing {intent}: {exc}")

