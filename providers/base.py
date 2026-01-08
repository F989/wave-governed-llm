from __future__ import annotations
from dataclasses import dataclass
from typing import List, Protocol, Optional, Dict, Any

@dataclass
class LLMAnswer:
    text: str
    citations: List[str]
    meta: Optional[Dict[str, Any]] = None

class LLMProvider(Protocol):
    name: str
    def answer(self, user_text: str, evidence: List[str], damping: float) -> LLMAnswer: ...

