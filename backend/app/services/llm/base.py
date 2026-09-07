from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Common interface so the generation backend can be swapped via env
    vars. All prompts flow through here — this is the single choke point
    where document text (untrusted data) and system instructions are kept
    clearly separated (see services/rag/prompts.py).

    Implementations should set self.last_input_tokens / self.last_output_tokens
    after each generate() call when the underlying API reports usage, so
    callers can log/aggregate real token counts (see analytics). Leave as
    None if the provider doesn't expose usage — callers must handle that.
    """

    last_input_tokens: int | None = None
    last_output_tokens: int | None = None

    @abstractmethod
    def generate(self, system: str, user: str, max_tokens: int = 1024) -> str:
        ...
