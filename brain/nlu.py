import json
import re
from dataclasses import dataclass
from difflib import get_close_matches
from importlib import import_module
from typing import TYPE_CHECKING, Any, Dict, List, Optional, List

from memory.sqlite_store import SQLiteMemory

if TYPE_CHECKING:
    from .llm_client import LLMClient


@dataclass
class ParsedCommand:
    intent: str
    slots: Dict[str, Any]
    raw_text: str
    language: str = "unknown"
    confidence: float = 0.0
    workflow: Optional[List[Dict[str, Any]]] = None  # For multi-step tasks
    requires_confirmation: bool = False


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
- HELP: {}                                # show capabilities
If unclear, use intent "SMALL_TALK" with {"response": "..."}.

Hindi examples (map them to intents above):
- "Sikha, Chrome kholo" -> {"intent": "OPEN_APPLICATION", "slots": {"app_name": "chrome"}}
- "YouTube kholo" -> {"intent": "OPEN_WEBSITE", "slots": {"query": "youtube"}}
- "Google pe Python course search karo" -> {"intent": "GOOGLE_SEARCH", "slots": {"query": "Python course"}}
- "YouTube pe Arijit Singh ke gaane search karo" -> {"intent": "YOUTUBE_SEARCH", "slots": {"query": "Arijit Singh songs"}}
- "YouTube pe lo-fi music chalao" -> {"intent": "YOUTUBE_PLAY", "slots": {"query": "lofi music"}}
- "Mere liye ek note banao: kal subah jaldi uthna hai" -> {"intent": "CREATE_NOTE", "slots": {"content": "kal subah jaldi uthna hai"}}
- "Madad" -> {"intent": "HELP", "slots": {}}
"""


# Intent Aliases
OPEN_ALIASES = ["open", "launch", "start", "kholo", "chalu karo"]
CLOSE_ALIASES = ["close", "stop", "band karo", "band kar do"]
SEARCH_ALIASES = ["search", "dhundo", "search karo"]
PLAY_ALIASES = ["play", "chalao", "gaana chalao", "video chalao"]
CREATE_ALIASES = ["create", "make", "banao", "ek banao"]
LIST_ALIASES = ["list", "show", "my", "dikhao", "mere"]
READ_ALIASES = ["read", "padho"]
SEND_ALIASES = ["send", "bhejo"]
TAKE_ALIASES = ["take", "lo"]
COMPLETE_ALIASES = ["complete", "mark", "done", "khatam"]

# Application Knowledge Base
APP_MAP = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
    "excel": "excel",
    "word": "winword",
    "powerpoint": "powerpnt",
    "notepad": "notepad",
    "calculator": "calc",
    "vscode": "code",
    "visual studio code": "code",
    "spotify": "spotify",
    "vlc": "vlc",
    "paint": "mspaint",
    "cmd": "cmd",
    "command prompt": "cmd",
}

# Dangerous intents requiring confirmation
DANGEROUS_INTENTS = {"SEND_EMAIL", "DELETE_FILE", "INSTALL_PROGRAM", "DOWNLOAD_FILE"}


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
                confidence=0.9,
                requires_confirmation=intent in DANGEROUS_INTENTS,
            )

        llm = self._get_llm()
        if llm is not None:
            try:
                response = llm.complete_json(SYSTEM_PROMPT, cleaned_text or text)
                data = json.loads(response)
                intent = data.get("intent", "UNKNOWN")
                return ParsedCommand(
                    intent=intent,
                    slots=data.get("slots", {}),
                    raw_text=text,
                    language=language,
                    confidence=0.7,
                    requires_confirmation=intent in DANGEROUS_INTENTS,
                )
            except Exception as exc:
                self._llm_error = str(exc)

        data = self._parse_locally(cleaned_text or text, language)
        return ParsedCommand(
            intent=data.get("intent", "UNKNOWN"),
            slots=data.get("slots", {}),
            raw_text=text,
            language=language,
            confidence=data.get("confidence", 0.5),
            requires_confirmation=data.get("intent", "UNKNOWN") in DANGEROUS_INTENTS,
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
            *(TAKE_ALIASES + ["screenshot", "screen shot"]),
        ):
            return {"intent": "TAKE_SCREENSHOT", "slots": {}, "confidence": 0.8}

        if self._matches_any(
            normalized,
            *(LIST_ALIASES + ["notes"]),
        ):
            return {"intent": "LIST_NOTES", "slots": {}, "confidence": 0.8}

        if self._matches_any(
            normalized,
            *(READ_ALIASES + ["emails", "check email", "gmail"]),
        ):
            return {"intent": "READ_EMAILS", "slots": {"limit": 5}, "confidence": 0.8}

        if self._matches_any(
            normalized,
            "what do you see",
            "describe scene",
            "camera",
            "what can you see",
            "kya dikh raha hai",
            "samne kya hai",
        ):
            return {"intent": "DESCRIBE_SCENE", "slots": {}, "confidence": 0.8}

        note_content = self._extract_after_prefix(
            raw,
            *(CREATE_ALIASES + ["note"]),
        )
        if note_content:
            return {"intent": "CREATE_NOTE", "slots": {"content": note_content}, "confidence": 0.7}

        website_target = self._extract_open_target(normalized)
        if website_target:
            website_targets = {"youtube", "google", "gmail", "facebook", "instagram", "github"}
            if website_target.lower() in website_targets:
                return {"intent": "OPEN_WEBSITE", "slots": {"query": website_target}, "confidence": 0.8}
            app_name = self._fuzzy_match_app(website_target)
            if app_name:
                return {"intent": "OPEN_APPLICATION", "slots": {"app_name": app_name}, "confidence": 0.7}
            return {"intent": "OPEN_APPLICATION", "slots": {"app_name": website_target}, "confidence": 0.5}

        task_content = self._extract_after_prefix(
            raw,
            *(CREATE_ALIASES + ["task"]),
        )
        if task_content:
            return {"intent": "CREATE_TASK", "slots": {"description": task_content}, "confidence": 0.7}

        if self._matches_any(
            normalized,
            *(LIST_ALIASES + ["tasks"]),
        ):
            status = "done" if "done" in normalized or "completed" in normalized else None
            if "pending" in normalized or "baaki" in normalized:
                status = "pending"
            return {"intent": "LIST_TASKS", "slots": {"status": status, "limit": 10}, "confidence": 0.8}

        task_id = self._extract_task_id(normalized)
        if task_id is not None and self._matches_any(
            normalized,
            *(COMPLETE_ALIASES + ["task"]),
        ):
            return {"intent": "COMPLETE_TASK", "slots": {"task_id": task_id}, "confidence": 0.7}

        youtube_play = self._extract_after_prefix(
            raw,
            *(PLAY_ALIASES + ["on youtube", "youtube"]),
        )
        if youtube_play:
            return {"intent": "YOUTUBE_PLAY", "slots": {"query": youtube_play}, "confidence": 0.7}

        youtube_search_match = re.search(
            r"youtube\s+(?:pe|par)\s+(.+?)\s+search\s+karo",
            normalized,
        )
        if youtube_search_match:
            return {
                "intent": "YOUTUBE_SEARCH",
                "slots": {"query": youtube_search_match.group(1).strip()},
                "confidence": 0.6,
            }

        youtube_search = self._extract_after_prefix(
            raw,
            *(SEARCH_ALIASES + ["youtube for", "on youtube", "youtube"]),
        )
        if youtube_search:
            return {"intent": "YOUTUBE_SEARCH", "slots": {"query": youtube_search}, "confidence": 0.7}

        google_search_match = re.search(
            r"google\s+(?:pe|par)\s+(.+?)\s+search\s+karo",
            normalized,
        )
        if google_search_match:
            return {
                "intent": "GOOGLE_SEARCH",
                "slots": {"query": google_search_match.group(1).strip()},
                "confidence": 0.6,
            }

        reverse_google_match = re.search(
            r"(.+?)\s+google\s+(?:pe|par)\s+search\s+karo",
            normalized,
        )
        if reverse_google_match:
            return {
                "intent": "GOOGLE_SEARCH",
                "slots": {"query": reverse_google_match.group(1).strip()},
                "confidence": 0.6,
            }

        google_query = self._extract_after_prefix(
            raw,
            *(SEARCH_ALIASES + ["google for", "google"]),
        )
        if google_query:
            return {"intent": "GOOGLE_SEARCH", "slots": {"query": google_query}, "confidence": 0.7}

        app_name = self._extract_after_prefix(
            raw,
            *(OPEN_ALIASES + ["app", "application"]),
        )
        if app_name:
            website_targets = {"youtube", "google", "gmail", "facebook", "instagram", "github"}
            if app_name.lower() in website_targets:
                return {"intent": "OPEN_WEBSITE", "slots": {"query": app_name}, "confidence": 0.8}
            fuzzy_app = self._fuzzy_match_app(app_name)
            if fuzzy_app:
                return {"intent": "OPEN_APPLICATION", "slots": {"app_name": fuzzy_app}, "confidence": 0.7}
            return {"intent": "OPEN_APPLICATION", "slots": {"app_name": app_name}, "confidence": 0.6}

        close_name = self._extract_after_prefix(raw, *(CLOSE_ALIASES + ["app", "application"]))
        if close_name:
            fuzzy_app = self._fuzzy_match_app(close_name)
            if fuzzy_app:
                close_name = fuzzy_app
            return {"intent": "CLOSE_APPLICATION", "slots": {"app_name": close_name}, "confidence": 0.7}

        url_match = re.search(r"https?://\S+", raw)
        if url_match:
            return {"intent": "OPEN_WEBSITE", "slots": {"url": url_match.group(0)}, "confidence": 0.9}

        # Send email
        send_match = re.search(r"send\s+email\s+to\s+(.+?)\s+about\s+(.+)", raw, re.IGNORECASE)
        if send_match:
            to = send_match.group(1).strip()
            subject = send_match.group(2).strip()
            return {"intent": "SEND_EMAIL", "slots": {"to": to, "subject": subject}, "confidence": 0.7}

        # Help
        if self._matches_any(normalized, "help", "what can you do", "commands", "madad", "kya kar sakti ho"):
            return {"intent": "HELP", "slots": {}, "confidence": 0.8}

        return {
            "intent": "SMALL_TALK",
            "slots": {
                "response": self._reply_for_language(
                    language,
                    "I can help with apps, web search, notes, tasks, screenshots, email, and vision. Say 'help' for more.",
                    "Main apps, web search, notes, tasks, screenshot, email aur vision mein help kar sakti hoon. 'Madad' kahiye aur janiye.",
                )
            },
            "confidence": 0.3,
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
        aliases = "|".join(OPEN_ALIASES)
        patterns = [
            rf"^(.+?)\s+(?:{aliases})$",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
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
    def _fuzzy_match_app(app_name: str) -> str | None:
        app_name_lower = app_name.lower()
        if app_name_lower in APP_MAP:
            return APP_MAP[app_name_lower]
        matches = get_close_matches(app_name_lower, APP_MAP.keys(), n=1, cutoff=0.6)
        if matches:
            return APP_MAP[matches[0]]
        return None

    @staticmethod
    def _contains_devanagari(text: str) -> bool:
        return any("\u0900" <= ch <= "\u097f" for ch in text)

    def _detect_language(self, text: str) -> str:
        if NLU._contains_devanagari(text):
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

