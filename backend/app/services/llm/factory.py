from functools import lru_cache

from app.core.config import get_settings
from app.services.llm.base import LLMProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()

    if settings.LLM_PROVIDER == "openai":
        from app.services.llm.openai_provider import OpenAILLMProvider

        return OpenAILLMProvider(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_LLM_MODEL)

    if settings.LLM_PROVIDER == "gemini":
        from app.services.llm.gemini_provider import GeminiProvider

        return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)

    from app.services.llm.anthropic_provider import AnthropicProvider

    return AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY, model=settings.ANTHROPIC_MODEL)
