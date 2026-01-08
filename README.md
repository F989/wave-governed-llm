# wave-governed-llm

Evidence-gated governance for language models, inspired by wave physics and energy dissipation.

This project explores a **fail-closed control layer for LLMs** that decides **whether a model is allowed to answer** and **how cautiously**, based on evidence strength and ambiguity — instead of filtering or correcting outputs after generation.

---

## Motivation

Large language models often hallucinate when evidence is weak, missing, or the request is ambiguous.  
Most mitigation approaches attempt to fix this *after* text is generated.

This project takes a different approach:

> **Do not generate unless the system is confident it should.**

Generation is *permissioned*, not corrected.

---

## Governance States

Each request is routed into one of three states:

- 🟢 **FREE** — strong evidence  
  → full response allowed

- 🟡 **DAMPEN** — partial or weak evidence  
  → cautious, minimal response

- 🔴 **PROJECT** — no evidence or ambiguous query  
  → ask for clarification (**Q**) or return unknown (**U**)

This makes the system **fail-closed by design**.

---

## How It Works (High Level)

1. **Evidence scoring**  
   `evidence_score()` assigns a score ∈ [0,1] based on:
   - quantity of evidence
   - relevance to user intent
   - concreteness

2. **Energy computation**
   ```text
   rho_text = 1 - evidence_score
   rho = blend(rho_text, rho_mask)

