from anthropic import Anthropic

from app.services.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        self.client = Anthropic(api_key=api_key)
        self.model = model

        def generate(self, system: str, user: str, max_tokens: int = 1024) -> str:
            response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if response.usage:
            self.last_input_tokens = response.usage.input_tokens
            self.last_output_tokens = response.usage.output_tokens
        return "".join(block.text for block in response.content if block.type == "text")
