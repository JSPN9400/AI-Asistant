import json
import re
from dataclasses import dataclass
from importlib import import_module
from typing import TYPE_CHECKING, Any, Dict

from memory.sqlite_store import SQLiteMemory

if TYPE_CHECKING:
    from .llm_client import LLMClient


@dataclass
class ParsedCommand:
    intent: str
    slots: Dict[str, Any]
    raw_text: str
    language: str = "unknown"


SYSTEM_PROMPT = """
You are the NLU brain for a desktop AI assistant named Sikha.
Sikha understands English and Hindi (Hinglish mixed is OK).

You MUST respond with pure JSON: {"intent": "...", "slots": {...}}.

Supported intents (examples):
- OPEN_APPLICATION: {"app_name": "chrome" }
- CLOSE_APPLICATION: {"app_name": "spotify" }
- OPEN_WEBSITE: {"url": "https://..." } or {"query": "youtube"}
- GOOGLE_SEARCH: {"query": "..."}
- YOUTUBE_SEARCH: {"query": "..."}        # search on YouTube
- YOUTUBE_PLAY: {"query": "..."}          # open or play a YouTube video
- TAKE_SCREENSHOT: {}
- READ_EMAILS: {"limit": 5}
- SEND_EMAIL: {"to": "...", "subject": "...", "body": "..."}
- CREATE_NOTE: {"content": "..."}
- LIST_NOTES: {}
- DESCRIBE_SCENE: {}
- CREATE_TASK: {"description": "..."}
- LIST_TASKS: {"status": "pending" | "done", "limit": 10}
- COMPLETE_TASK: {"task_id": 1}
If unclear, use intent "SMALL_TALK" with {"response": "..."}.

Hindi examples (map them to intents above):
- "Sikha, Chrome kholo" -> {"intent": "OPEN_APPLICATION", "slots": {"app_name": "chrome"}}
- "YouTube kholo" -> {"intent": "OPEN_WEBSITE", "slots": {"query": "youtube"}}
- "Google pe Python course search karo" -> {"intent": "GOOGLE_SEARCH", "slots": {"query": "Python course"}}
- "YouTube pe Arijit Singh ke gaane search karo" -> {"intent": "YOUTUBE_SEARCH", "slots": {"query": "Arijit Singh songs"}}
- "YouTube pe lo-fi music chalao" -> {"intent": "YOUTUBE_PLAY", "slots": {"query": "lofi music"}}
- "Mere liye ek note banao: kal subah jaldi uthna hai" -> {"intent": "CREATE_NOTE", "slots": {"content": "kal subah jaldi uthna hai"}}
"""


class NLU:
    def __init__(
        self,
        llm: "LLMClient | None" = None,
        memory: SQLiteMemory | None = None,
    ):
        self.llm = llm
        self.memory = memory or SQLiteMemory()
        self._llm_error: str | None = None

    def parse(self, text: str) -> ParsedCommand:
        cleaned_text = self._strip_wake_word(text)
        language = self._detect_language(cleaned_text or text)
        learned = self._lookup_learned_command(cleaned_text)
        if learned is not None:
            intent, slots = learned
            return ParsedCommand(
                intent=intent,
                slots=slots,
                raw_text=text,
                language=language,
            )

        llm = self._get_llm()
        if llm is not None:
            try:
                response = llm.complete_json(SYSTEM_PROMPT, cleaned_text or text)
                data = json.loads(response)
                return ParsedCommand(
                    intent=data.get("intent", "UNKNOWN"),
                    slots=data.get("slots", {}),
                    raw_text=text,
                    language=language,
                )
            except Exception as exc:
                self._llm_error = str(exc)

        data = self._parse_locally(cleaned_text or text, language)
        return ParsedCommand(
            intent=data.get("intent", "UNKNOWN"),
            slots=data.get("slots", {}),
            raw_text=text,
            language=language,
        )

    def learn_from_result(self, parsed: ParsedCommand, success: bool) -> None:
        if not success or parsed.intent in {"SMALL_TALK", "UNKNOWN"}:
            return
        normalized = self._normalize_text(self._strip_wake_word(parsed.raw_text))
        if not normalized:
            return
        slots = {k: v for k, v in parsed.slots.items() if not k.startswith("_")}
        self.memory.remember_command(
            phrase=normalized,
            intent=parsed.intent,
            slots=slots,
            language=parsed.language,
        )

    def _get_llm(self) -> "LLMClient | None":
        if self.llm is not None:
            return self.llm
        if self._llm_error is not None:
            return None
        try:
            llm_module = import_module("brain.llm_client")
            self.llm = llm_module.LLMClient()
        except Exception as exc:
            self._llm_error = str(exc)
            return None
        return self.llm

    def _parse_locally(self, text: str, language: str) -> Dict[str, Any]:
        raw = text.strip()
        normalized = self._normalize_text(raw)

        if not normalized:
            return {
                "intent": "SMALL_TALK",
                "slots": {
                    "response": self._reply_for_language(
                        language,
                        "Please say that again.",
                        "Please repeat that.",
                    )
                },
            }

        if self._matches_any(
            normalized,
            "take screenshot",
            "screenshot",
            "screen shot",
            "screenshot lo",
            "screen shot lo",
        ):
            return {"intent": "TAKE_SCREENSHOT", "slots": {}}

        if self._matches_any(
            normalized,
            "list notes",
            "show notes",
            "my notes",
            "notes dikhao",
            "mere notes",
        ):
            return {"intent": "LIST_NOTES", "slots": {}}

        if self._matches_any(
            normalized,
            "read emails",
            "read email",
            "check email",
            "gmail",
            "email padho",
            "emails dikhao",
        ):
            return {"intent": "READ_EMAILS", "slots": {"limit": 5}}

        if self._matches_any(
            normalized,
            "what do you see",
            "describe scene",
            "camera",
            "what can you see",
            "kya dikh raha hai",
            "samne kya hai",
        ):
            return {"intent": "DESCRIBE_SCENE", "slots": {}}

        note_content = self._extract_after_prefix(
            raw,
            "create a note",
            "create note",
            "make a note",
            "note",
            "save note",
            "note banao",
            "ek note banao",
        )
        if note_content:
            return {"intent": "CREATE_NOTE", "slots": {"content": note_content}}

        website_target = self._extract_open_target(normalized)
        if website_target:
            website_targets = {"youtube", "google", "gmail", "facebook", "instagram", "github"}
            if website_target.lower() in website_targets:
                return {"intent": "OPEN_WEBSITE", "slots": {"query": website_target}}
            return {"intent": "OPEN_APPLICATION", "slots": {"app_name": website_target}}

        task_content = self._extract_after_prefix(
            raw,
            "create task",
            "add task",
            "new task",
            "task",
            "task banao",
            "ek task banao",
        )
        if task_content:
            return {"intent": "CREATE_TASK", "slots": {"description": task_content}}

        if self._matches_any(
            normalized,
            "list tasks",
            "show tasks",
            "my tasks",
            "tasks dikhao",
            "mere tasks",
        ):
            status = "done" if "done" in normalized or "completed" in normalized else None
            if "pending" in normalized or "baaki" in normalized:
                status = "pending"
            return {"intent": "LIST_TASKS", "slots": {"status": status, "limit": 10}}

        task_id = self._extract_task_id(normalized)
        if task_id is not None and self._matches_any(
            normalized,
            "complete task",
            "mark task",
            "done task",
            "task complete",
            "task khatam",
        ):
            return {"intent": "COMPLETE_TASK", "slots": {"task_id": task_id}}

        youtube_play = self._extract_after_prefix(
            raw,
            "play on youtube",
            "play youtube",
            "youtube play",
            "play",
            "youtube pe chalao",
            "gaana chalao",
            "video chalao",
        )
        if youtube_play:
            return {"intent": "YOUTUBE_PLAY", "slots": {"query": youtube_play}}

        youtube_search_match = re.search(
            r"youtube\s+(?:pe|par)\s+(.+?)\s+search\s+karo",
            normalized,
        )
        if youtube_search_match:
            return {
                "intent": "YOUTUBE_SEARCH",
                "slots": {"query": youtube_search_match.group(1).strip()},
            }

        youtube_search = self._extract_after_prefix(
            raw,
            "search youtube for",
            "youtube search",
            "search on youtube",
            "youtube pe search karo",
            "youtube par search karo",
        )
        if youtube_search:
            return {"intent": "YOUTUBE_SEARCH", "slots": {"query": youtube_search}}

        google_search_match = re.search(
            r"google\s+(?:pe|par)\s+(.+?)\s+search\s+karo",
            normalized,
        )
        if google_search_match:
            return {
                "intent": "GOOGLE_SEARCH",
                "slots": {"query": google_search_match.group(1).strip()},
            }

        reverse_google_match = re.search(
            r"(.+?)\s+google\s+(?:pe|par)\s+search\s+karo",
            normalized,
        )
        if reverse_google_match:
            return {
                "intent": "GOOGLE_SEARCH",
                "slots": {"query": reverse_google_match.group(1).strip()},
            }

        google_query = self._extract_after_prefix(
            raw,
            "search google for",
            "google search",
            "search for",
            "google pe search karo",
            "google par search karo",
            "dhundo",
        )
        if google_query:
            return {"intent": "GOOGLE_SEARCH", "slots": {"query": google_query}}

        app_name = self._extract_after_prefix(
            raw,
            "open app",
            "open application",
            "start app",
            "launch",
            "open",
            "khol do",
            "kholo",
            "chalu karo",
        )
        if app_name:
            website_targets = {"youtube", "google", "gmail", "facebook", "instagram", "github"}
            if app_name.lower() in website_targets:
                return {"intent": "OPEN_WEBSITE", "slots": {"query": app_name}}
            return {"intent": "OPEN_APPLICATION", "slots": {"app_name": app_name}}

        close_name = self._extract_after_prefix(raw, "close", "stop", "band karo", "band kar do")
        if close_name:
            return {"intent": "CLOSE_APPLICATION", "slots": {"app_name": close_name}}

        url_match = re.search(r"https?://\S+", raw)
        if url_match:
            return {"intent": "OPEN_WEBSITE", "slots": {"url": url_match.group(0)}}

        return {
            "intent": "SMALL_TALK",
            "slots": {
                "response": self._reply_for_language(
                    language,
                    "I can help with apps, web search, notes, tasks, screenshots, email, and vision.",
                    "Main apps, web search, notes, tasks, screenshot, email aur vision mein help kar sakti hoon.",
                )
            },
        }

    def _lookup_learned_command(self, text: str) -> tuple[str, Dict[str, Any]] | None:
        normalized = self._normalize_text(text)
        if not normalized:
            return None
        learned = self.memory.get_learned_command(normalized)
        if learned is None:
            return None
        intent, slots, _language = learned
        return intent, slots

    @staticmethod
    def _matches_any(text: str, *phrases: str) -> bool:
        return any(phrase in text for phrase in phrases)

    @staticmethod
    def _extract_open_target(text: str) -> str | None:
        patterns = [
            r"^(.+?)\s+(?:kholo|khol do|kholdo|open)$",
            r"^(.+?)\s+(?:chalu karo|start karo)$",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip(" :,-")
        return None

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(text.lower().split())

    @staticmethod
    def _extract_after_prefix(text: str, *prefixes: str) -> str | None:
        lowered = NLU._normalize_text(text)
        for prefix in prefixes:
            if lowered.startswith(prefix):
                value = text[len(prefix):].strip(" :,-")
                return value or None
        return None

    @staticmethod
    def _strip_wake_word(text: str) -> str:
        cleaned = text.strip()
        pattern = re.compile(r"^\s*(sikha|shikha|sikhaa)\b[\s,:-]*", re.IGNORECASE)
        return pattern.sub("", cleaned, count=1).strip()

    @staticmethod
    def _contains_devanagari(text: str) -> bool:
        return any("\u0900" <= ch <= "\u097f" for ch in text)

    def _detect_language(self, text: str) -> str:
        if self._contains_devanagari(text):
            return "hindi"

        normalized = self._normalize_text(text)
        hindi_markers = {
            "kya", "kaise", "mera", "meri", "mere", "kholo", "band", "dikhao",
            "padho", "banao", "chalao", "karo", "hai", "haan", "nahi",
        }
        english_markers = {
            "open", "close", "search", "play", "note", "task", "email",
            "website", "application", "show", "read", "take",
        }
        hindi_hits = sum(1 for marker in hindi_markers if marker in normalized.split())
        english_hits = sum(1 for marker in english_markers if marker in normalized.split())

        if hindi_hits and english_hits:
            return "hinglish"
        if hindi_hits:
            return "hindi"
        if english_hits:
            return "english"
        return "unknown"

    @staticmethod
    def _reply_for_language(language: str, english_text: str, hindi_text: str) -> str:
        return hindi_text if language in {"hindi", "hinglish"} else english_text

    @staticmethod
    def _extract_task_id(text: str) -> int | None:
        match = re.search(r"\btask\s+(\d+)\b", text)
        if match:
            return int(match.group(1))
        match = re.search(r"\b(\d+)\b", text)
        if match:
            return int(match.group(1))
        return None

