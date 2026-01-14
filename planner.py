# planner.py
from __future__ import annotations

import re
from action_plan import ActionPlan, PlannedAction

SENSITIVE_RE = re.compile(r"\b(password|api\s*key|secret|token|credential)\b", re.IGNORECASE)

# "send / post / upload / publish / webhook / request / call" + רמז ליעד חיצוני
EXTERNAL_SEND_RE = re.compile(
    r"\b(send|email|post|upload|publish|forward|share|exfiltrate|leak|webhook|http|https|request|call)\b",
    re.IGNORECASE,
)

EXTERNAL_TARGET_RE = re.compile(
    r"\b(external|server|endpoint|url|domain|third[-\s]*party|outside|remote)\b|https?://",
    re.IGNORECASE,
)

# כתיבה/שינוי state – רק אם יש גם יעד טיפוסי (db/file/profile/etc.)
WRITE_VERB_RE = re.compile(r"\b(write|update|delete|modify|commit|save|insert|overwrite)\b", re.IGNORECASE)
WRITE_TARGET_RE = re.compile(r"\b(database|db|table|record|row|file|disk|profile|repo|repository|git)\b", re.IGNORECASE)

def plan_from_text(user_text: str) -> ActionPlan:
    t = user_text.strip()

    touches_sensitive = bool(SENSITIVE_RE.search(t))

    # external send = יש פועל של שליחה + יעד חיצוני (או url)
    has_send_verb = bool(EXTERNAL_SEND_RE.search(t))
    has_external_target = bool(EXTERNAL_TARGET_RE.search(t))
    external_send = has_send_verb and has_external_target

    # writes_state = פועל כתיבה + יעד state ממשי
    has_write_verb = bool(WRITE_VERB_RE.search(t))
    has_write_target = bool(WRITE_TARGET_RE.search(t))
    writes_state = has_write_verb and has_write_target

    actions = [
        PlannedAction(type="respond", name="respond_to_user", args={"text": t})
    ]

    return ActionPlan(
        intent="respond",
        actions=actions,
        touches_sensitive_data=touches_sensitive,
        requires_external_send=external_send,
        writes_state=writes_state,
    )


