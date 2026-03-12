from __future__ import annotations

import json
import os
from urllib import error, request

from dotenv import load_dotenv


class LLMClient:
    def __init__(self, model: str | None = None, api_key_env: str = "GEMINI_API_KEY"):
        load_dotenv()
        self.provider = self._resolve_provider()
        self.api_key_env = api_key_env
        if self.provider == "ollama":
            self.model_name = model or os.getenv("OLLAMA_MODEL", "phi3")
            self.ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
            return

        self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key in environment variable {api_key_env}")

        try:
            from google import genai
            from google.genai import types
        except Exception as exc:
            raise RuntimeError("google-genai is not available in this environment.") from exc

        self._genai = genai
        self._types = types
        self.client = self._genai.Client(api_key=api_key)

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        if self.provider == "ollama":
            prompt = (
                system_prompt.strip()
                + "\n\nUser command:\n"
                + user_prompt.strip()
                + "\n\nRemember: respond with ONLY valid JSON."
            )
            return self._ollama_generate(prompt, response_format="json")

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=(
                system_prompt.strip()
                + "\n\nUser command:\n"
                + user_prompt.strip()
                + "\n\nRemember: respond with ONLY valid JSON."
            ),
            config=self._types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return response.text

    def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        if self.provider == "ollama":
            return self._ollama_generate(user_prompt, system_prompt=system_prompt)

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=f"{system_prompt.strip()}\n\nUser:\n{user_prompt.strip()}",
        )
        return response.text

    @staticmethod
    def _resolve_provider() -> str:
        provider = os.getenv("ASSISTANT_LLM_PROVIDER", "").strip().lower()
        if provider in {"gemini", "ollama"}:
            return provider
        if os.getenv("OLLAMA_MODEL"):
            return "ollama"
        return "gemini"

    def _ollama_generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        response_format: str | None = None,
    ) -> str:
        payload: dict[str, object] = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt
        if response_format == "json":
            payload["format"] = "json"

        endpoint = f"{self.ollama_host}/api/generate"
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except error.URLError as exc:
            raise RuntimeError(
                f"Ollama is unavailable at {self.ollama_host}. Start Ollama and ensure model '{self.model_name}' is installed."
            ) from exc

        text = str(body.get("response", "")).strip()
        if not text:
            raise RuntimeError(f"Ollama returned an empty response for model '{self.model_name}'.")
        return text


def get_llm_status() -> dict[str, str]:
    load_dotenv()
    provider = LLMClient._resolve_provider()

    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "phi3")
        host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        endpoint = f"{host}/api/tags"
        req = request.Request(endpoint, method="GET")
        try:
            with request.urlopen(req, timeout=5) as response:
                body = json.loads(response.read().decode("utf-8"))
            models = [item.get("name", "") for item in body.get("models", [])]
            available = any(name == model or name.startswith(f"{model}:") for name in models)
            message = "Phi-3 is ready." if available else f"Ollama is running, but model '{model}' was not found."
        except Exception as exc:
            available = False
            message = f"Ollama check failed: {exc}"
        return {
            "provider": "ollama",
            "model": model,
            "available": str(available).lower(),
            "message": message,
        }

    api_key = os.getenv("GEMINI_API_KEY", "")
    available = bool(api_key)
    return {
        "provider": "gemini",
        "model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        "available": str(available).lower(),
        "message": "Gemini API key found." if available else "Set GEMINI_API_KEY to enable Gemini.",
    }
