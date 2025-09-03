from typing import List, Dict
import re

def _clean_text(text: str) -> str:
    # Basic whitespace normalization
    return re.sub(r"\s+", " ", text).strip()

def summarize_history_for_context(history: List[Dict], max_chars: int = 1200) -> str:
    """
    Lightweight extractive summary:
    - Keeps earliest user intent
    - Captures last assistant advice
    - Includes the most recent turns until it hits the max length
    """
    if not history:
        return ""

    user_first = next((m["content"] for m in history if m["role"] == "user"), "")
    assistant_last = next((m["content"] for m in reversed(history) if m["role"] == "assistant"), "")

    blocks = []
    if user_first:
        blocks.append(f"Initial user intent: { _clean_text(user_first) }")
    if assistant_last:
        blocks.append(f"Latest assistant advice: { _clean_text(assistant_last) }")

    # add recent messages from the end backwards
    recent = []
    for m in reversed(history[-10:]):  # last up to 10 turns
        role = m["role"]
        txt = _clean_text(m["content"])
        if txt and f"{role}: {txt}" not in recent:
            recent.append(f"{role}: {txt}")
    recent = list(reversed(recent))

    blocks.append("Recent exchanges:\n" + "\n".join(recent))

    summary = "\n\n".join(blocks)
    if len(summary) <= max_chars:
        return summary

    # Trim if needed
    return summary[: max_chars - 100] + "\n… (truncated)"
