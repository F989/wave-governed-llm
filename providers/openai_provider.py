from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional

from openai import OpenAI

from providers.base import LLMProvider, LLMResponse


@dataclass
class OpenAIProvider(LLMProvider):
    """
    OpenAI-backed provider.
    Expects OPENAI_API_KEY to be set in the environment (PowerShell: $env:OPENAI_API_KEY="...").

    This provider *enforces* governance:
    - FREE   -> fuller answer allowed
    - DAMPEN -> short, cautious, evidence-cited answer (hard length + formatting constraints)
    """
    model: str = "gpt-4o-mini"
    temperature: float = 0.0  # lower = fewer hallucinations
    max_tokens_free: int = 450
    max_tokens_dampen: int = 140
    _client: Optional[OpenAI] = field(default=None, init=False, repr=False)

    def _get_client(self) -> OpenAI:
        if self._client is not None:
            return self._client

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. "
                "Set it in your shell (e.g., PowerShell: $env:OPENAI_API_KEY='...')"
            )

        self._client = OpenAI(api_key=api_key)
        return self._client

    def answer(self, user_text: str, evidence: List[str], damping: float) -> LLMResponse:
        client = self._get_client()

        is_free = (damping == 0)
        gov_mode = "FREE" if is_free else f"DAMPEN (damping={damping:.3f})"

        # Number evidence so the model can cite [1], [2], ...
        if evidence:
            evidence_block = "\n".join(f"[{i+1}] {e}" for i, e in enumerate(evidence))
        else:
            evidence_block = "(none)"

        max_tokens = self.max_tokens_free if is_free else self.max_tokens_dampen

        system = (
            "You are a careful assistant.\n"
            "You MUST use ONLY the provided evidence.\n"
            "Do NOT use outside knowledge.\n"
            "Do NOT guess.\n"
            "If evidence is missing/insufficient, say so and request what is needed.\n"
        )

        # Governance-specific style constraints
        if is_free:
            style_rules = (
                "Style rules (FREE):\n"
                "- You may answer normally, but ONLY from the evidence.\n"
                "- If you make a claim, it must be supported by at least one evidence item.\n"
            )
        else:
            style_rules = (
                "Style rules (DAMPEN):\n"
                "- Respond with AT MOST 3 bullet points.\n"
                "- Each bullet MUST cite at least one evidence item like [1] or [2].\n"
                "- No filler, no introductions, no extra formatting.\n"
                "- If you cannot answer safely from the evidence, say 'Insufficient evidence' "
                "and list exactly what evidence is missing (1–2 items).\n"
                "- Do NOT infer or extrapolate. If not explicitly stated in evidence, say 'Insufficient evidence' and list missing evidence (1–2 items).\n"
            )

        user_prompt = (
            f"Governance mode: {gov_mode}\n\n"
            f"{style_rules}\n"
            f"User request: {user_text}\n\n"
            "Evidence:\n"
            f"{evidence_block}\n\n"
            "Answer now."
        )

        try:
            resp = client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
            )
            text = (resp.choices[0].message.content or "").strip()
        except Exception as e:
            # Fail-closed: controlled output
            text = f"Provider error: {type(e).__name__}: {e}"

        # Keep citations transparent: return the original evidence list
        return LLMResponse(text=text, citations=evidence)


