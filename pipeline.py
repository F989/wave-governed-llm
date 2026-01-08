import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from wave_metrics import rho_energy, entropy, max_weight, l2
from wave_governor import decide
from toy_attention import governed_attention

from providers.echo_provider import EchoProvider
from providers.base import LLMProvider

from evidence_score import evidence_score


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
    provider: Optional[LLMProvider] = None,   # ✅ added
) -> RunResult:
    """
    Runs a single governance + toy-attention + provider pass.

    rho is primarily evidence-driven:
      rho_text = 1 - evidence_score
    optionally blended with absorber knob (mask)
    """
    evidence = evidence or []
    np.random.seed(seed)

    d = 5
    C = np.random.randn(d)

    if mask is None:
        mask = np.array([0.7, 0.4, 0.2, 0.0, 0.2])

    # -------------------------
    # Evidence-driven rho (primary)
    # -------------------------
    ev = evidence_score(user_text, evidence)
    rho_text = 1.0 - float(ev["score"])

    # Absorber knob (secondary) — but if evidence is decent, mask should matter less
    A = mask * C
    rho_mask = rho_energy(C, A)

    mask_weight = 0.10 if ev["score"] >= 0.50 else 0.25
    rho = min(1.0, (1.0 - mask_weight) * rho_text + mask_weight * rho_mask)

    # -------------------------
    # governance decision
    # -------------------------
    gd = decide(user_text, rho)

    # -------------------------
    # toy attention setup
    # -------------------------
    n_keys = 6
    keys = np.random.randn(n_keys, d)
    values = np.random.randn(n_keys, d)

    # "FREE/DAMPEN": compute attention
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

    # -------------------------
    # interference measurement (only if not projected)
    # -------------------------
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
    # generate output via provider (modular)
    # -------------------------
    if provider is None:
        provider = EchoProvider()

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
            "provider": getattr(provider, "name", "unknown"),
        }

    metrics = {
        "rho_energy": rho,
        "rho_text": rho_text,
        "rho_mask": rho_mask,
        "mask": mask.tolist(),
        "evidence_score": ev,   # includes reasons + subscores
        "attention": att,
        "interference": interference,
    }

    return RunResult(
        decision={"mode": gd.mode, "damping": gd.damping, "project_state": gd.state},
        metrics=metrics,
        output=output
    )


