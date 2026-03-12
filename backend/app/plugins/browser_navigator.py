from __future__ import annotations

from urllib.parse import quote_plus

from app.plugins.base import BasePlugin, PluginContext


KNOWN_DESTINATIONS = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "github": "https://github.com",
}


class BrowserNavigatorPlugin(BasePlugin):
    name = "browser_navigator"
    description = "Handles assistant-style open, search, and navigation requests."
    supported_actions = ["open_url", "google_search", "youtube_search", "youtube_play"]
    input_fields = ["action", "target", "query", "url"]
    output_fields = ["message", "action", "url"]

    def execute(self, parameters: dict, context: PluginContext) -> dict:
        action = parameters.get("action", "open_url")
        target = str(parameters.get("target", "")).strip().lower()
        query = str(parameters.get("query", "")).strip()
        url = str(parameters.get("url", "")).strip()

        if action == "google_search":
            final_url = "https://www.google.com/search?q=" + quote_plus(query or target)
            return {
                "status": "success",
                "message": f"Searching Google for {query or target}.",
                "action": "open_url",
                "url": final_url,
            }

        if action in {"youtube_search", "youtube_play"}:
            final_url = "https://www.youtube.com/results?search_query=" + quote_plus(query or target)
            verb = "Playing" if action == "youtube_play" else "Searching YouTube for"
            return {
                "status": "success",
                "message": f"{verb} {query or target}.",
                "action": "open_url",
                "url": final_url,
            }

        if not url and target:
            url = KNOWN_DESTINATIONS.get(target, "")
            if not url:
                url = "https://www.google.com/search?q=" + quote_plus(target)

        if not url:
            return {
                "status": "error",
                "message": "I need a site or search target to open.",
            }

        return {
            "status": "success",
            "message": f"Opening {target or url}.",
            "action": "open_url",
            "url": url,
        }
