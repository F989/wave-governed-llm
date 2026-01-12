# pipeline.py
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from wave_metrics import rho_energy, entropy, max_weight, l2
from wave_governor import decide
from toy_attention import governed_attention

from providers.echo_provider import EchoProvider
from providers.base import LLMProvider

from evidence_score import evidence_score

# Action-gateway layer
from planner import plan_from_text
from behavior_monitor import monitor
from policy_engine import evaluate_policy


@dataclass
class RunResult:
    decision: Dict[str, Any]
    metrics: Dict[str, Any]
    output: Dict[str, Any]


def run_case(
    user_text: str,
    evidence: Optional[List[str]] = None,
    mask: Optional[np.ndarray] = None,
    seed: int = 0,
    provider: Optional[LLMProvider] = None,
) -> RunResult:
    evidence = evidence or []
    np.random.seed(seed)

    d = 5
    C = np.random.randn(d)

    if mask is None:
        mask = np.array([0.7, 0.4, 0.2, 0.0, 0.2])

    # -------------------------
    # Evidence-driven rho
    # -------------------------
    ev = evidence_score(user_text, evidence)
    rho_text = 1.0 - float(ev["score"])

    A = mask * C
    rho_mask = rho_energy(C, A)

    mask_weight = 0.10 if ev["score"] >= 0.50 else 0.25
    rho = min(1.0, (1.0 - mask_weight) * rho_text + mask_weight * rho_mask)

    # -------------------------
    # governance decision
    # -------------------------
    gd = decide(user_text, rho)

    # -------------------------
    # toy attention + interference (only if not projected)
    # -------------------------
    n_keys = 6
    keys = np.random.randn(n_keys, d)
    values = np.random.randn(n_keys, d)

    if gd.mode != "PROJECT":
        out, w, _scores = governed_attention(C, keys, values, gd.damping)
        att = {
            "entropy": entropy(w),
            "max_weight": max_weight(w),
            "weights": np.round(w, 3).tolist(),
        }
    else:
        out, w = None, None
        att = {"entropy": None, "max_weight": None, "weights": None}

    if gd.mode != "PROJECT":
        W1 = np.random.randn(d, d)
        Q1, _ = np.linalg.qr(W1)
        W2 = np.random.randn(d, d)
        Q2, _ = np.linalg.qr(W2)

        S1 = Q1 @ C
        S2 = Q2 @ C

        out1, w1, _ = governed_attention(S1, keys, values, gd.damping)
        out2, w2, _ = governed_attention(S2, keys, values, gd.damping)

        interference = {
            "I_out": l2(out1, out2),
            "I_w": l2(w1, w2),
        }
    else:
        interference = {"I_out": None, "I_w": None}

    # -------------------------
    # provider default
    # -------------------------
    if provider is None:
        provider = EchoProvider()

    # -------------------------
    # ✅ ALWAYS: Plan → Monitor → Policy (even if PROJECT)
    # -------------------------
    plan_dict = None
    monitor_dict = None
    policy_dict = None

    try:
        plan = plan_from_text(user_text)
        plan_dict = {
            "intent": plan.intent,
            "actions": [{"type": a.type, "name": a.name, "args": a.args} for a in plan.actions],
            "touches_sensitive_data": plan.touches_sensitive_data,
            "requires_external_send": plan.requires_external_send,
            "writes_state": plan.writes_state,
        }

        report = monitor(plan)
        monitor_dict = {"risk_flags": report.risk_flags}

        pol = evaluate_policy(report)  # policy expects MonitorResult
        policy_dict = {"allow": pol.allow, "reasons": pol.reasons}

        # Fail-closed: if policy blocks -> return BLOCKED immediately
        if not pol.allow:
            output = {
                "state": "BLOCKED",
                "text": "Blocked by policy engine.",
                "policy": policy_dict,
                "plan": plan_dict,
                "monitor": monitor_dict,
            }

            metrics = {
                "rho_energy": rho,
                "rho_text": rho_text,
                "rho_mask": rho_mask,
                "mask": mask.tolist(),
                "evidence_score": ev,
                "attention": att,
                "interference": interference,
                "action_plan": plan_dict,
                "behavior_monitor": monitor_dict,
                "policy": policy_dict,
            }

            return RunResult(
                decision={"mode": gd.mode, "damping": gd.damping, "project_state": gd.state},
                metrics=metrics,
                output=output,
            )

    except Exception as e:
        # Fail-closed: if gate crashes -> block
        output = {
            "state": "BLOCKED",
            "text": f"Policy gate error: {type(e).__name__}: {e}",
        }
        metrics = {
            "rho_energy": rho,
            "rho_text": rho_text,
            "rho_mask": rho_mask,
            "mask": mask.tolist(),
            "evidence_score": ev,
            "attention": att,
            "interference": interference,
            "policy_gate_error": f"{type(e).__name__}: {e}",
            "action_plan": plan_dict,
            "behavior_monitor": monitor_dict,
            "policy": policy_dict,
        }
        return RunResult(
            decision={"mode": gd.mode, "damping": gd.damping, "project_state": gd.state},
            metrics=metrics,
            output=output,
        )

    # -------------------------
    # If governor projects, return that (but with policy telemetry present)
    # -------------------------
    if gd.mode == "PROJECT":
        output = {
            "state": gd.state,
            "text": gd.message,
            "missing": gd.missing,
        }
    else:
        ans = provider.answer(user_text, evidence, gd.damping)
        output = {
            "state": "K",
            "text": ans.text,
            "citations": ans.citations,
            "damping": gd.damping,
            "provider": getattr(provider, "name", provider.__class__.__name__),
        }

    metrics = {
        "rho_energy": rho,
        "rho_text": rho_text,
        "rho_mask": rho_mask,
        "mask": mask.tolist(),
        "evidence_score": ev,
        "attention": att,
        "interference": interference,
        "action_plan": plan_dict,
        "behavior_monitor": monitor_dict,
        "policy": policy_dict,
    }

    return RunResult(
        decision={"mode": gd.mode, "damping": gd.damping, "project_state": gd.state},
        metrics=metrics,
        output=output
    )




