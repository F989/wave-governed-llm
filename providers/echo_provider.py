from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from .base import LLMAnswer

@dataclass
class EchoProvider:
    """
    Safe default provider for GitHub:
    - No external API keys
    - Demonstrates evidence-gated behavior
    """
    name: str = "echo"

    def answer(self, user_text: str, evidence: List[str], damping: float) -> LLMAnswer:
        if not evidence:
            return LLMAnswer(
                text="No evidence provided → governed system will not generate an answer.",
                citations=[],
                meta={"mode": "blocked_no_evidence"}
            )

        lines = []
        mode = "FREE" if damping == 0 else "DAMPEN"
        lines.append(f"- Governance mode: {mode} (damping={damping:.3f})")
        lines.append(f"- User request: {user_text}")
        lines.append("- Evidence summary:")
        for i, e in enumerate(evidence, start=1):
            lines.append(f"  [{i}] {e}")

        lines.append("- Response:")
        if damping > 0.40:
            lines.append("  Evidence is partial → returning a minimal, cautious response. Add stronger evidence for detail.")
        else:
            lines.append("  Evidence is sufficient → returning a fuller response bounded by the evidence above.")

        citations = [f"[{i}]" for i in range(1, len(evidence) + 1)]
        return LLMAnswer(text="\n".join(lines), citations=citations, meta={"provider": self.name})
