from __future__ import annotations

import json
from typing import Any
from urllib import error, parse, request

from app.config import settings


class LLMGateway:
    def is_configured(self) -> bool:
        if not settings.enable_cloud_reasoner:
            return False
        if settings.llm_provider == "ollama":
            return True
        return bool(settings.gemini_api_key)

    def status(self) -> dict[str, str]:
        if not settings.enable_cloud_reasoner:
            return {
                "provider": settings.llm_provider,
                "model": settings.ollama_model if settings.llm_provider == "ollama" else settings.gemini_model,
                "available": "false",
                "message": "Cloud reasoner disabled. Using deterministic fallback routing.",
            }
        if settings.llm_provider == "ollama":
            try:
                req = request.Request(f"{settings.ollama_host.rstrip('/')}/api/tags", method="GET")
                with request.urlopen(req, timeout=5) as response:
                    body = json.loads(response.read().decode("utf-8"))
                models = [item.get("name", "") for item in body.get("models", [])]
                available = any(
                    name == settings.ollama_model or name.startswith(f"{settings.ollama_model}:")
                    for name in models
                )
                message = (
                    f"Ollama model '{settings.ollama_model}' is ready."
                    if available
                    else f"Ollama is reachable, but model '{settings.ollama_model}' is unavailable."
                )
                return {
                    "provider": "ollama",
                    "model": settings.ollama_model,
                    "available": str(available).lower(),
                    "message": message,
                }
            except Exception as exc:
                return {
                    "provider": "ollama",
                    "model": settings.ollama_model,
                    "available": "false",
                    "message": f"Ollama check failed: {exc}",
                }

        return {
            "provider": "gemini",
            "model": settings.gemini_model,
            "available": str(bool(settings.gemini_api_key)).lower(),
            "message": "Gemini API key found." if settings.gemini_api_key else "Set GEMINI_API_KEY to enable Gemini.",
        }

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        if settings.llm_provider == "ollama":
            return self._complete_ollama_json(system_prompt, user_prompt)
        if settings.gemini_api_key:
            return self._complete_gemini_json(system_prompt, user_prompt)
        raise RuntimeError("No LLM provider is configured.")

    def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        if settings.llm_provider == "ollama":
            return self._complete_ollama_text(system_prompt, user_prompt)
        if settings.gemini_api_key:
            return self._complete_gemini_text(system_prompt, user_prompt)
        raise RuntimeError("No LLM provider is configured.")

    def _complete_ollama_json(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": settings.ollama_model,
            "system": system_prompt,
            "prompt": user_prompt,
            "format": "json",
            "stream": False,
        }
        endpoint = f"{settings.ollama_host.rstrip('/')}/api/generate"
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
        return str(body.get("response", "")).strip()

    def _complete_ollama_text(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": settings.ollama_model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
        }
        endpoint = f"{settings.ollama_host.rstrip('/')}/api/generate"
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
        return str(body.get("response", "")).strip()

    def _complete_gemini_json(self, system_prompt: str, user_prompt: str) -> str:
        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent?key={parse.quote(settings.gemini_api_key)}"
        )
        payload: dict[str, Any] = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                system_prompt.strip()
                                + "\n\nUser command:\n"
                                + user_prompt.strip()
                                + "\n\nReturn valid JSON only."
                            )
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
            },
        }
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Gemini request failed: {detail or exc.reason}") from exc

        candidates = body.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini returned no candidates.")
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise RuntimeError("Gemini returned no content parts.")
        return str(parts[0].get("text", "")).strip()

    def _complete_gemini_text(self, system_prompt: str, user_prompt: str) -> str:
        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent?key={parse.quote(settings.gemini_api_key)}"
        )
        payload: dict[str, Any] = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{system_prompt.strip()}\n\nUser:\n{user_prompt.strip()}",
                        }
                    ]
                }
            ]
        }
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Gemini request failed: {detail or exc.reason}") from exc

        candidates = body.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini returned no candidates.")
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise RuntimeError("Gemini returned no content parts.")
        return str(parts[0].get("text", "")).strip()
