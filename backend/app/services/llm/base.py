from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Common interface so the generation backend can be swapped via env
    vars. All prompts flow through here — this is the single choke point
    where document text (untrusted data) and system instructions are kept
    clearly separated (see services/rag/prompts.py)."""

    @abstractmethod
    def generate(self, system: str, user: str, max_tokens: int = 1024) -> str:
        ...
