from dataclasses import dataclass
from typing import List
from behavior_monitor import MonitorResult

@dataclass
class PolicyDecision:
    allow: bool
    reasons: List[str]

def evaluate_policy(
    monitor_result: MonitorResult,
    allow_writes: bool = False,
    allow_external_send: bool = False,
) -> PolicyDecision:
    reasons: List[str] = []
    flags = set(monitor_result.risk_flags)

    if "external_send" in flags and not allow_external_send:
        reasons.append("Blocked: external send not allowed")

    if "writes_state" in flags or "write_action" in flags:
        if not allow_writes:
            reasons.append("Blocked: write/state changes not allowed")

    if "sensitive_data" in flags:
        reasons.append("Sensitive data access requires human approval")

    if "too_many_actions" in flags:
        reasons.append("Too many actions without approval")

    return PolicyDecision(
        allow=(len(reasons) == 0),
        reasons=reasons
    )


