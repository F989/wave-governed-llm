from action_plan import ActionPlan, PlannedAction

def plan_from_text(user_text: str) -> ActionPlan:
    t = user_text.lower()

    touches_sensitive = any(k in t for k in ["password", "api key", "secret", "token"])
    external_send = any(k in t for k in ["send", "email", "post", "upload", "publish"])
    writes_state = any(k in t for k in ["delete", "update", "write", "modify", "commit"])

    actions = [PlannedAction(type="respond", name="respond_to_user", args={"text": user_text})]
    return ActionPlan(
        intent="respond",
        actions=actions,
        touches_sensitive_data=touches_sensitive,
        requires_external_send=external_send,
        writes_state=writes_state,
    )
