import numpy as np

from pipeline import run_case
from providers.echo_provider import EchoProvider
from providers.openai_provider import OpenAIProvider


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


def run_suite(provider):
    print("\n" + "#" * 80)
    print("RUNNING WITH PROVIDER:", provider.__class__.__name__, "| model:", getattr(provider, "model", None))
    print("#" * 80)

    masks = {
        "soft": np.array([0.9, 0.8, 0.7, 0.6, 0.5]),
        "mid":  np.array([0.7, 0.4, 0.2, 0.0, 0.2]),
        "hard": np.array([0.3, 0.1, 0.0, 0.0, 0.0]),
    }

    # Case 1: with evidence
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

    # Case 2: PROJECT -> Q (ambiguous)
    res_q = run_case(
        user_text="it?",
        evidence=[],
        mask=masks["hard"],
        seed=0,
        provider=provider,
    )
    print_result("CASE: hard mask + ambiguous user_text (PROJECT -> Q)", res_q)

    # Case 3: PROJECT -> U (no evidence)
    res_u = run_case(
        user_text="Tell me the capital of France.",
        evidence=[],
        mask=masks["hard"],
        seed=0,
        provider=provider,
    )
    print_result("CASE: hard mask + no evidence (PROJECT -> U)", res_u)

    # Case 4: minimal evidence (CRISPR)
    minimal_ev = [
        "Source: WHO (2021): Human germline genome editing is considered unethical at this time; calls for strong governance and broad societal consensus before any clinical use.",
        "Source: NASEM (2017): Germline editing might be permissible only under very strict conditions (serious disease, no reasonable alternatives, rigorous oversight) and is not ready for routine clinical use."
    ]

    res_ev = run_case(
        user_text="Based on current research, should CRISPR be used for human germline editing, and what are the long-term societal risks?",
        evidence=minimal_ev,
        mask=masks["hard"],
        seed=0,
        provider=provider,
    )
    print_result("CASE: hard mask + minimal evidence (CRISPR germline)", res_ev)


def main():
    # Run with EchoProvider (offline / deterministic)
    run_suite(EchoProvider())

    # Run with OpenAIProvider (real LLM)
    run_suite(OpenAIProvider())


if __name__ == "__main__":
    main()




