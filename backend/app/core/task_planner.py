"""Task planning layer for multi-step workflows.

This module sits between the high-level task reasoner and the plugin execution layer.
It detects compound user intents and expands them to a short workflow so that the
assistant can perform multi-step actions (e.g., "download python installer and install it").

The planner is intentionally simple and heuristic-based; it is designed to grow over time.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from app.schemas.task import StructuredTask


def plan(user_input: str, structured_task: StructuredTask) -> Optional[Dict[str, Any]]:
    """Return a workflow plan for a multi-step request, or None for simple tasks."""

    # Only create a workflow for multi-step request patterns.
    normalized = (user_input or "").strip()
    if not normalized:
        return None

    lowered = normalized.lower()

    # Pattern: "download X and install it"
    match = re.search(r"download\s+(.+?)\s+and\s+install", lowered)
    if match:
        item = match.group(1).strip()
        query = item
        if "installer" not in item:
            query = f"{item} installer"

        workflow: List[Dict[str, Any]] = [
            {
                "intent": "web_search",
                "parameters": {"query": query},
            },
            {
                "intent": "browser_navigator",
                "parameters": {"action": "google_search", "query": query},
            },
            {
                "intent": "desktop_control",
                "parameters": {"action": "install_program", "target": item},
                "requires_confirmation": True,
            },
        ]
        return {"workflow": workflow}

    # Pattern: "delete file <path>" or "delete <path>"
    match = re.search(r"\bdelete\s+(?:file\s+)?(.+)$", lowered)
    if match and " and " not in lowered:
        path = match.group(1).strip()
        workflow = [
            {
                "intent": "desktop_control",
                "parameters": {"action": "delete_file", "target": path},
                "requires_confirmation": True,
            }
        ]
        return {"workflow": workflow}

    # Pattern: "send email" combined with phrase like "and" (e.g., "draft and send email")
    if "send email" in lowered and " and " in lowered:
        workflow = [
            {
                "intent": "email_writer",
                "parameters": {"prompt": normalized},
                "requires_confirmation": True,
            }
        ]
        return {"workflow": workflow}

    return None
