from __future__ import annotations
from dataclasses import dataclass
from typing import List

from action_plan import ActionPlan

@dataclass
class MonitorResult:
    risk_flags: List[str]

def monitor(plan: ActionPlan) -> MonitorResult:
    flags: List[str] = []

    # דגלים בסיסיים — תוסיף לפי צורך
    if plan.requires_external_send:
        flags.append("external_send")

    if plan.touches_sensitive_data:
        flags.append("sensitive_data")

    if plan.writes_state:
        flags.append("writes_state")

    if len(plan.actions) > 3:
        flags.append("too_many_actions")

    # כתיבה למקור (רעיון בסיסי)
    if any(a.type == "write" for a in plan.actions):
        flags.append("write_action")

    return MonitorResult(risk_flags=flags)
