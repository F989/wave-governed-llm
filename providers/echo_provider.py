from dataclasses import dataclass
from typing import List

from .base import LLMProvider, LLMResponse


@dataclass
class EchoProvider(LLMProvider):
    """
    Minimal provider for debugging:
    returns a response that echoes the user request + evidence.
    """

    name: str = "echo"

    def answer(self, user_text: str, evidence: List[str], damping: float) -> LLMResponse:
        mode = "FREE" if damping == 0 else f"DAMPEN(damping={damping:.3f})"

        lines = []
        lines.append(f"- Governance mode: {mode}")
        lines.append(f"- User request: {user_text}")

        lines.append("- Evidence summary:")
        if evidence:
            for i, e in enumerate(evidence, 1):
                lines.append(f"  [{i}] {e}")
        else:
            lines.append("  (none)")

        lines.append("- Response:")
        if evidence:
            lines.append("  Evidence is sufficient → returning a fuller response bounded by the evidence above.")
        else:
            lines.append("  Evidence is missing → cannot answer beyond stating what is missing.")

        return LLMResponse(text="\n".join(lines), citations=evidence)

