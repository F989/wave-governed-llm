import numpy as np

from pipeline import run_case
from providers.echo_provider import EchoProvider


def _r(x):
    return None if x is None else round(float(x), 3)


def print_result(title: str, res):
    print("\n" + "=" * 80)
    print(title)

    # decision
    print("- decision:", res.decision)

    # key metrics
    att = res.metrics.get("attention", {})
    inter = res.metrics.get("interference", {})
    ev = res.metrics.get("evidence_score", {})

    ev_score = ev.get("score", None)
    ev_reasons = ev.get("reasons", [])
    ev_signals = ev.get("signals", {})
    subs = (ev_signals.get("subscores") or {})

    print(
        "- metrics:",
        "rho=", _r(res.metrics.get("rho_energy")),
        "| rho_text=", _r(res.metrics.get("rho_text")),
        "| rho_mask=", _r(res.metrics.get("rho_mask")),
        "| evidence_score=", _r(ev_score),
        "| H=", _r(att.get("entropy")),
        "| max_w=", _r(att.get("max_weight")),
        "| I_out=", _r(inter.get("I_out")),
        "| I_w=", _r(inter.get("I_w")),
    )

    # evidence details
    if ev_score is not None:
        print("  evidence reasons:", ev_reasons)
        if subs:
            print("  evidence subscores:", {k: _r(v) for k, v in subs.items()})

    # output
    print("- output state:", res.output["state"])
    print(res.output["text"])
    if "missing" in res.output:
        print("missing:", res.output["missing"])


def main():
    provider = EchoProvider()   # ✅ modular provider (can be swapped)

    masks = {
        "soft": np.array([0.9, 0.8, 0.7, 0.6, 0.5]),
        "mid":  np.array([0.7, 0.4, 0.2, 0.0, 0.2]),
        "hard": np.array([0.3, 0.1, 0.0, 0.0, 0.0]),
    }

    user_text = "Write a rejection note with actionable feedback."
    evidence = [
        "Role requires strong SQL and stakeholder communication.",
        "Interview notes: candidate solved SQL tasks but struggled explaining tradeoffs; asked for clarifications; limited product sense discussion."
    ]

    for name, mask in masks.items():
        res = run_case(
            user_text=user_text,
            evidence=evidence,
            mask=mask,
            seed=0,
            provider=provider,
        )
        print_result(f"CASE: {name.upper()} mask (with evidence)", res)

    # PROJECT -> Q (ambiguous)
    res_q = run_case(
        user_text="it?",
        evidence=[],
        mask=masks["hard"],
        seed=0,
        provider=provider,
    )
    print_result("CASE: hard mask + ambiguous user_text (PROJECT -> Q)", res_q)

    # PROJECT -> U (no evidence)
    res_u = run_case(
        user_text="Tell me the capital of France.",
        evidence=[],
        mask=masks["hard"],
        seed=0,
        provider=provider,
    )
    print_result("CASE: hard mask + no evidence (PROJECT -> U)", res_u)

    # Minimal evidence moves off PROJECT
    minimal_ev = [ "Source: Britannica: The capital of France is Paris.",
  "Paris is the political and administrative capital of France."]
    res_ev = run_case(
        user_text="Tell me the capital of France.",
        evidence=minimal_ev,
        mask=masks["hard"],
        seed=0,
        provider=provider,
    )
    print_result("CASE: hard mask + minimal evidence (should move off PROJECT)", res_ev)


if __name__ == "__main__":
    main()



