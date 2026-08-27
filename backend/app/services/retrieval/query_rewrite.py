"""
Query rewriting: turns a follow-up question plus recent conversation history
into a standalone query suitable for retrieval, e.g.

    History: "What is the attendance requirement?" -> "75%."
    Follow-up: "What about students with medical reasons?"
    Rewritten: "What are the attendance exceptions for students with medical reasons?"

If there's no history, or the LLM call fails, the original message is used
as-is so query rewriting is never a hard dependency for the pipeline to work.
"""
from __future__ import annotations

from app.services.llm.factory import get_llm_provider

SYSTEM_PROMPT = (
    "You rewrite follow-up questions into standalone search queries using the "
    "conversation history. Output ONLY the rewritten query, nothing else. "
    "If the latest message is already standalone, return it unchanged."
)


def rewrite_query(message: str, history: list[dict]) -> str:
    if not history:
        return message

    history_text = "\n".join(f"{h['role']}: {h['content']}" for h in history[-6:])
    prompt = f"Conversation history:\n{history_text}\n\nLatest message: {message}\n\nStandalone query:"

    try:
        llm = get_llm_provider()
        rewritten = llm.generate(system=SYSTEM_PROMPT, user=prompt, max_tokens=120).strip()
        return rewritten if rewritten else message
    except Exception:
        return message
