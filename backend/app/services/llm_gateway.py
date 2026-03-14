from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from urllib import error, parse, request

from app.config import settings


class LLMGateway:
    _last_status: dict[str, str] | None = None

    def is_configured(self) -> bool:
        if not settings.enable_cloud_reasoner:
            return False
        if settings.llm_provider == "openai":
            return bool(settings.openai_api_key)
        if settings.llm_provider == "ollama":
            return True
        return bool(settings.gemini_api_key)

    def status(self) -> dict[str, str]:
        status = self._current_status()
        if self._last_status and self._matches_current_selection(self._last_status):
            status.update(
                {
                    "state": self._last_status.get("state", status["state"]),
                    "message": self._last_status.get("message", status["message"]),
                    "checked_at": self._last_status.get("checked_at"),
                }
            )
        return status

    def configure(self, *, provider: str, model: str, enable_cloud_reasoner: bool) -> dict[str, object]:
        provider_name = provider.strip().lower()
        if provider_name not in {"ollama", "openai", "gemini"}:
            raise ValueError("Provider must be one of: ollama, openai, gemini.")

        model_name = model.strip()
        if not model_name:
            raise ValueError("Model name is required.")

        settings.enable_cloud_reasoner = enable_cloud_reasoner
        settings.llm_provider = provider_name
        if provider_name == "ollama":
            settings.ollama_model = model_name
        elif provider_name == "openai":
            settings.openai_model = model_name
        else:
            settings.gemini_model = model_name

        self._last_status = None
        return {
            "provider": provider_name,
            "model": model_name,
            "enable_cloud_reasoner": settings.enable_cloud_reasoner,
            "enable_auto_routing": settings.enable_auto_llm_routing,
            "status": self.status(),
        }

    # High-level helpers that can choose a provider per task when auto routing is enabled.
    def complete_text_for_task(self, task_name: str, system_prompt: str, user_prompt: str) -> str:
        provider = self._select_provider_for_task(task_name)
        return self._complete_text_for_provider(provider, system_prompt, user_prompt)

    def complete_json_for_task(self, task_name: str, system_prompt: str, user_prompt: str) -> str:
        provider = self._select_provider_for_task(task_name)
        return self._complete_json_for_provider(provider, system_prompt, user_prompt)

    def check(self) -> dict[str, str]:
        status = self._current_status()
        status["checked_at"] = datetime.now(UTC).isoformat()
        if not settings.enable_cloud_reasoner:
            self._last_status = status
            return status

        if settings.llm_provider == "ollama":
            self._last_status = status
            return status

        if settings.llm_provider == "openai":
            checked = self._check_openai(status)
            self._last_status = checked
            return checked

        checked = self._check_gemini(status)
        self._last_status = checked
        return checked

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        # Backwards-compatible: use the globally selected provider.
        return self._complete_json_for_provider(settings.llm_provider, system_prompt, user_prompt)

    def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        # Backwards-compatible: use the globally selected provider.
        return self._complete_text_for_provider(settings.llm_provider, system_prompt, user_prompt)

    @staticmethod
    def _configured_model_name() -> str:
        if settings.llm_provider == "openai":
            return settings.openai_model
        if settings.llm_provider == "ollama":
            return settings.ollama_model
        return settings.gemini_model

    def _current_status(self) -> dict[str, str]:
        if not settings.enable_cloud_reasoner:
            return {
                "provider": settings.llm_provider,
                "model": self._configured_model_name(),
                "available": "false",
                "state": "disabled",
                "message": "Cloud reasoner disabled. Using deterministic fallback routing.",
                "checked_at": None,
            }
        if settings.llm_provider == "openai":
            available = bool(settings.openai_api_key)
            return {
                "provider": "openai",
                "model": settings.openai_model,
                "available": str(available).lower(),
                "state": "configured" if available else "missing_key",
                "message": "OpenAI API key found." if available else "Set OPENAI_API_KEY to enable OpenAI.",
                "checked_at": None,
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
                    "state": "ready" if available else "missing_model",
                    "message": message,
                    "checked_at": None,
                }
            except Exception as exc:
                return {
                    "provider": "ollama",
                    "model": settings.ollama_model,
                    "available": "false",
                    "state": "offline",
                    "message": f"Ollama check failed: {exc}",
                    "checked_at": None,
                }

        available = bool(settings.gemini_api_key)
        return {
            "provider": "gemini",
            "model": settings.gemini_model,
            "available": str(available).lower(),
            "state": "configured" if available else "missing_key",
            "message": "Gemini API key found." if available else "Set GEMINI_API_KEY to enable Gemini.",
            "checked_at": None,
        }

    def _check_openai(self, base_status: dict[str, str]) -> dict[str, str]:
        if not settings.openai_api_key:
            return base_status
        try:
            from openai import OpenAI
        except Exception as exc:
            return {
                **base_status,
                "available": "false",
                "state": "package_missing",
                "message": f"openai package is unavailable: {exc}",
            }

        try:
            client = OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "Reply with READY only."},
                    {"role": "user", "content": "ready"},
                ],
                max_tokens=3,
            )
            content = response.choices[0].message.content or ""
            return {
                **base_status,
                "available": "true",
                "state": "ready",
                "message": f"OpenAI responded successfully with {settings.openai_model}.",
            }
        except Exception as exc:
            message = str(exc)
            lowered = message.lower()
            if "insufficient_quota" in lowered or "quota" in lowered or "429" in lowered:
                state = "exhausted"
            else:
                state = "offline"
            return {
                **base_status,
                "available": "false",
                "state": state,
                "message": message,
            }

    def _check_gemini(self, base_status: dict[str, str]) -> dict[str, str]:
        if not settings.gemini_api_key:
            return base_status
        try:
            self._complete_gemini_text("Reply with READY only.", "ready")
            return {
                **base_status,
                "available": "true",
                "state": "ready",
                "message": f"Gemini responded successfully with {settings.gemini_model}.",
            }
        except Exception as exc:
            message = str(exc)
            lowered = message.lower()
            if "quota" in lowered or "429" in lowered or "resource_exhausted" in lowered:
                state = "exhausted"
            else:
                state = "offline"
            return {
                **base_status,
                "available": "false",
                "state": state,
                "message": message,
            }

    def _matches_current_selection(self, status: dict[str, str]) -> bool:
        return status.get("provider") == settings.llm_provider and status.get("model") == self._configured_model_name()

    def _select_provider_for_task(self, task_name: str) -> str:
        """
        Simple heuristic routing:
        - General Q&A and chat -> prefer OpenAI / Gemini if configured.
        - Long-form reports and summaries -> prefer Gemini, else OpenAI, else Ollama.
        - Desktop / browser control and web search -> Ollama (local, cheaper).
        Falls back to globally selected provider when auto routing is disabled.
        """
        if not settings.enable_cloud_reasoner or not settings.enable_auto_llm_routing:
            return settings.llm_provider

        task = (task_name or "").lower()

        # Control / tools: keep them on the local model.
        if task in {"desktop_control", "browser_navigator", "web_search"}:
            return "ollama"

        # Reporting / summarization style tasks: prefer Gemini > OpenAI > Ollama.
        if task in {"sales_report_generator", "meeting_notes_summarizer", "excel_data_analyzer"}:
            if settings.gemini_api_key:
                return "gemini"
            if settings.openai_api_key:
                return "openai"
            return "ollama"

        # General assistant / small talk and default.
        if settings.openai_api_key:
            return "openai"
        if settings.gemini_api_key:
            return "gemini"
        return "ollama"

    def _complete_json_for_provider(self, provider: str, system_prompt: str, user_prompt: str) -> str:
        provider_name = (provider or "").strip().lower() or settings.llm_provider
        if provider_name == "openai":
            return self._complete_openai_json(system_prompt, user_prompt)
        if provider_name == "ollama":
            return self._complete_ollama_json(system_prompt, user_prompt)
        if provider_name == "gemini" and settings.gemini_api_key:
            return self._complete_gemini_json(system_prompt, user_prompt)
        raise RuntimeError("No LLM provider is configured.")

    def _complete_text_for_provider(self, provider: str, system_prompt: str, user_prompt: str) -> str:
        provider_name = (provider or "").strip().lower() or settings.llm_provider
        if provider_name == "openai":
            return self._complete_openai_text(system_prompt, user_prompt)
        if provider_name == "ollama":
            return self._complete_ollama_text(system_prompt, user_prompt)
        if provider_name == "gemini" and settings.gemini_api_key:
            return self._complete_gemini_text(system_prompt, user_prompt)
        raise RuntimeError("No LLM provider is configured.")

    def _complete_openai_json(self, system_prompt: str, user_prompt: str) -> str:
        try:
            from openai import OpenAI
        except Exception as exc:
            raise RuntimeError("openai package is unavailable in this environment.") from exc

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("OpenAI returned an empty JSON response.")
        return content

    def _complete_openai_text(self, system_prompt: str, user_prompt: str) -> str:
        try:
            from openai import OpenAI
        except Exception as exc:
            raise RuntimeError("openai package is unavailable in this environment.") from exc

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("OpenAI returned an empty text response.")
        return content.strip()

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
