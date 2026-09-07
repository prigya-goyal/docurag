from google import genai
from google.genai import types

from app.services.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    """Google Gemini provider. Uses the free-tier-eligible Flash models by
    default — see https://ai.google.dev for current free tier rate limits."""

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(self, system: str, user: str, max_tokens: int = 1024) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                max_output_tokens=max(max_tokens, 2048),
            ),
        )
        text = response.text
        if not text:
            # Thinking (or a safety filter) consumed the whole budget with nothing
            # left for visible output. Surface this clearly instead of returning "".
            finish_reason = None
            if response.candidates:
                finish_reason = response.candidates[0].finish_reason
            raise RuntimeError(f"Gemini returned no output text (finish_reason={finish_reason}).")
        if response.usage_metadata:
            self.last_input_tokens = response.usage_metadata.prompt_token_count
            self.last_output_tokens = response.usage_metadata.candidates_token_count
        return text