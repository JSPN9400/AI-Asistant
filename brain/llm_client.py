
from __future__ import annotations

import json
import os
from urllib import request, error

from dotenv import load_dotenv
from assistant.paths import env_file_candidates


def _load_environment():
    for env_path in env_file_candidates():
        load_dotenv(dotenv_path=env_path, override=False)


class LLMClient:

    def __init__(self):
        _load_environment()

        # Use environment variables for keys to avoid leaking secrets in source control.
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")

        self.ollama_model = os.getenv("OLLAMA_MODEL", "phi3:mini")
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")

        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

        self._openai = None
        self._genai = None
        self._types = None

        if self.openai_key:
            try:
                from openai import OpenAI
                self._openai = OpenAI(api_key=self.openai_key)
            except Exception:
                pass

        if self.gemini_key:
            try:
                from google import genai
                from google.genai import types
                self._genai = genai
                self._types = types
                self._gemini = genai.Client(api_key=self.gemini_key)
            except Exception:
                pass


    # ----------------------------------------------------
    # TASK ROUTING
    # ----------------------------------------------------

    def route_provider(self, task: str) -> str:

        task = (task or "").lower()

        if task in {"desktop_control", "browser_navigator", "web_search"}:
            return "ollama"

        if task in {"file_analyzer", "excel_generator", "sales_report_generator"}:
            if self._genai:
                return "gemini"
            if self._openai:
                return "openai"
            return "ollama"

        if task in {"general_assistant", "email_writer"}:
            if self._openai:
                return "openai"
            if self._genai:
                return "gemini"
            return "ollama"

        if self._openai:
            return "openai"

        if self._genai:
            return "gemini"

        return "ollama"


    # ----------------------------------------------------
    # MAIN ENTRY
    # ----------------------------------------------------

    def complete_for_task(self, task: str, system_prompt: str, user_prompt: str):

        provider = self.route_provider(task)

        try:
            return self._call(provider, system_prompt, user_prompt)

        except Exception:

            # fallback order
            for fallback in ["openai", "gemini", "ollama"]:
                if fallback == provider:
                    continue
                try:
                    return self._call(fallback, system_prompt, user_prompt)
                except Exception:
                    continue

        raise RuntimeError("All LLM providers failed.")


    # ----------------------------------------------------
    # PROVIDER CALLS
    # ----------------------------------------------------

    def _call(self, provider, system_prompt, user_prompt):

        if provider == "openai" and self._openai:

            response = self._openai.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            return response.choices[0].message.content.strip()

        if provider == "gemini" and self._genai:

            response = self._gemini.models.generate_content(
                model=self.gemini_model,
                contents=f"{system_prompt}\n\nUser:\n{user_prompt}",
            )

            return response.text.strip()

        if provider == "ollama":

            return self._ollama_generate(system_prompt, user_prompt)

        raise RuntimeError(f"Provider {provider} unavailable")


    # ----------------------------------------------------
    # OLLAMA
    # ----------------------------------------------------

    def _ollama_generate(self, system_prompt, user_prompt):

        payload = {
            "model": self.ollama_model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
        }

        endpoint = f"{self.ollama_host}/api/generate"

        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=15) as res:
                body = json.loads(res.read().decode())

        except error.URLError as exc:
            raise RuntimeError("Ollama is not running or model missing.") from exc

        text = body.get("response", "").strip()

        if not text:
            raise RuntimeError("Ollama returned empty response.")

        return text


# ----------------------------------------------------
# STATUS CHECK
# ----------------------------------------------------

def get_llm_status():

    _load_environment()

    status = {}

    if os.getenv("OPENAI_API_KEY"):
        status["openai"] = "configured"
    else:
        status["openai"] = "missing key"

    if os.getenv("GEMINI_API_KEY"):
        status["gemini"] = "configured"
    else:
        status["gemini"] = "missing key"

    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

    try:
        request.urlopen(f"{host}/api/tags", timeout=3)
        status["ollama"] = "running"
    except Exception:
        status["ollama"] = "not running"

    return status