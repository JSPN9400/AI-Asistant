import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


class LLMClient:
    """
    Thin wrapper around a Gemini chat completion API.

    Uses the API key from GEMINI_API_KEY and model name from GEMINI_MODEL
    (default: gemini-2.0-flash or whatever you prefer).
    """

    def __init__(self, model: str | None = None, api_key_env: str = "GEMINI_API_KEY"):
        load_dotenv()
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise RuntimeError(
                f"Missing API key in environment variable {api_key_env}"
            )
        self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.client = genai.Client(api_key=api_key)

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        """
        Return the message content as a JSON string.
        """
        prompt = (
            system_prompt.strip()
            + "\n\nUser command:\n"
            + user_prompt.strip()
            + "\n\nRemember: respond with ONLY valid JSON."
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return response.text

