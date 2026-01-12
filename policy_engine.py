from __future__ import annotations
from dataclasses import dataclass
from typing import List, Literal

from behavior_monitor import MonitorResult

Policy = Literal["allow", "human_review", "block"]

@dataclass
class PolicyDecision:
    decision: Policy
    reasons: List[str]


def evaluate_policy(
    monitor_result: MonitorResult,
    allow_writes: bool = False,
    allow_external_send: bool = False,
) -> PolicyDecision:
    reasons: List[str] = []
    flags = set(monitor_result.risk_flags)

    # ❌ Hard blocks
    if "external_send" in flags and not allow_external_send:
        reasons.append("External send is not allowed")
        return PolicyDecision(decision="block", reasons=reasons)

    if "writes_state" in flags and not allow_writes:
        reasons.append("Write/state changes are not allowed")
        return PolicyDecision(decision="block", reasons=reasons)

    if "too_many_actions" in flags:
        reasons.append("Too many actions without approval")
        return PolicyDecision(decision="block", reasons=reasons)

    # 🧍 Human-in-the-loop
    if "sensitive_data" in flags:
        reasons.append("Sensitive data access requires human approval")
        return PolicyDecision(decision="human_review", reasons=reasons)

    # ✅ Safe
    return PolicyDecision(decision="allow", reasons=[])

