from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

ActionType = Literal["respond", "tool", "read", "write"]

@dataclass
class PlannedAction:
    type: ActionType
    name: str
    args: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ActionPlan:
    intent: str
    actions: List[PlannedAction] = field(default_factory=list)
    touches_sensitive_data: bool = False
    requires_external_send: bool = False
    writes_state: bool = False

    @staticmethod
    def minimal(intent: str, actions: List[PlannedAction]) -> "ActionPlan":
        return ActionPlan(intent=intent, actions=actions)
