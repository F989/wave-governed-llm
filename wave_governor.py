from dataclasses import dataclass
from typing import List, Optional
import re

VAGUE_WORDS = {"it", "this", "that", "they", "stuff"}

@dataclass
class GovernanceDecision:
    mode: str                 # FREE / DAMPEN / PROJECT
    damping: float            # 0.0 (FREE/PROJECT) or rho_energy (DAMPEN)
    state: Optional[str]      # None for FREE/DAMPEN, or "U"/"Q" for PROJECT
    message: Optional[str]    # user-facing text for PROJECT
    missing: List[str]        # what is needed to proceed


def is_ambiguous(text: str) -> bool:
    t = text.lower().strip()
    # extract word tokens (removes punctuation like "it?")
    words = re.findall(r"[a-z]+", t)

    if len(words) < 1:
        return True

    return (len(words) < 8) and any(w in VAGUE_WORDS for w in words)


def governance_mode(rho_energy: float, t_dampen: float = 0.30, t_project: float = 0.70) -> str:
    if rho_energy >= t_project:
        return "PROJECT"
    if rho_energy >= t_dampen:
        return "DAMPEN"
    return "FREE"


def decide(
    user_text: str,
    rho_energy: float,
    t_dampen: float = 0.30,   # ✅ FIX: was 0.10
    t_project: float = 0.70
) -> GovernanceDecision:
    mode = governance_mode(rho_energy, t_dampen=t_dampen, t_project=t_project)

    if mode == "FREE":
        return GovernanceDecision(mode="FREE", damping=0.0, state=None, message=None, missing=[])

    if mode == "DAMPEN":
        return GovernanceDecision(mode="DAMPEN", damping=rho_energy, state=None, message=None, missing=[])

    # PROJECT (fail-closed): no inference; return controlled response (U or Q)
    if is_ambiguous(user_text):
        return GovernanceDecision(
            mode="PROJECT",
            damping=0.0,
            state="Q",
            message="צריך הבהרה לפני שאפשר להמשיך. מה בדיוק הכוונה/מהו הקונטקסט? תני 1–2 פרטים או מקור.",
            missing=["clarification", "context"]
        )

    return GovernanceDecision(
        mode="PROJECT",
        damping=0.0,
        state="U",
        message="אין מספיק מידע/ראיות כדי לענות בביטחון. צריך מקור/נתונים/ציטוט קצר שעליו אפשר לבסס תשובה.",
        missing=["evidence/source", "quote or tool output"]
    )



