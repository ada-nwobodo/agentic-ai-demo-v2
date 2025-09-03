from dataclasses import dataclass
from typing import Optional

@dataclass
class LLMConfig:
    api_key: str
    model: str = "gpt-4o-mini"
    timeout: int = 60

class LLM:
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        if self.config.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.config.api_key)
            except Exception as e:
                self._client = None
                self._err = f"OpenAI client not available: {e}"
        else:
            self._err = "No API key provided; falling back to local echo mode."

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Uses OpenAI Chat Completions if API key is provided.
        Otherwise, returns a deterministic echo useful for DEV/QA.
        """
        if self._client is None:
            # Fallback: Local echo with a tiny heuristic so DEMO still works offline
            return (
                "⚠️ Running in offline mode (no API key).\n\n"
                "Here's a structured response based on your inputs:\n\n"
                f"**Understanding**: {user_prompt[:400]}...\n\n"
                "**Next steps**: 1) Provide an API key in the sidebar. 2) Set a model. 3) Re-run the message."
            )

        try:
            resp = self._client.chat.completions.create(
                model=self.config.model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                timeout=self.config.timeout,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"LLM error: {e}"
