# wave-governed-llm

Evidence-gated governance for language models, inspired by wave physics,
energy dissipation, and action-level safety.

This project explores a **fail-closed control layer for LLMs** that decides:

- **whether a model is allowed to answer**
- **how cautiously it should answer**
- **whether an action is allowed at all**

based on **evidence strength, ambiguity, and intended actions** —  
*before* any generation occurs.

---

## Motivation

Large language models often hallucinate or behave unsafely when:

- evidence is weak or missing
- the request is ambiguous
- the model is implicitly allowed to take actions it should not

Most mitigation approaches attempt to fix this *after* text is generated
(using filters, rewriters, or post-hoc moderation).

This project takes a different approach:

> **Do not generate unless the system is confident it should.**  
> **Do not act unless the action itself is allowed.**

Generation and actions are **permissioned**, not corrected.

---

## Core Ideas

1. **Evidence-first governance**  
   Confidence is derived from *evidence*, not model confidence.

2. **Fail-closed by design**  
   When in doubt → do less, ask, or refuse.

3. **Policy governs actions, not text**  
   Safety is enforced at the *intent/action level*, not by filtering words.

---

## Governance States (Evidence Layer)

Each request is routed into one of three high-level states:

- 🟢 **FREE** — strong evidence  
  → full response allowed

- 🟡 **DAMPEN** — partial or weak evidence  
  → cautious, minimal response

- 🔴 **PROJECT** — no evidence or ambiguous query  
  → ask for clarification (**Q**) or return unknown (**U**)

This layer controls *whether* the model may respond and *how strongly*.

---

## Action Gateway (Policy Layer)

After evidence-based gating, requests pass through an **Action Gateway**
that decides whether the **intended action itself is allowed**.

### High-level flow



