from __future__ import annotations

from dataclasses import dataclass
from typing import List, Protocol


@dataclass
class LLMResponse:
    text: str
    citations: List[str]


class LLMProvider(Protocol):
    """
    Provider interface.
    Any model (OpenAI/Ollama/Gemini/Echo) should implement this.
    """
    def answer(self, user_text: str, evidence: List[str], damping: float) -> LLMResponse:
        ...


