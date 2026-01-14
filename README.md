# wave-governed-llm

**Fail-closed governance + policy gating for LLM calls**, driven by evidence strength and simple action-risk heuristics.

This repository is a learning-oriented prototype that demonstrates how to **block / dampen / request clarification** *before* calling an LLM, rather than trying to “fix” unsafe or hallucinated output after generation.

> ⚠️ Important: The “wave / energy” terminology is **metaphorical** and used as an intuitive framing for **risk/uncertainty**.  
> The current implementation does **not** simulate real physical wave dynamics, nor does it hook into real model attention weights.

---

## What the project does (today)

### ✅ 1) Evidence-gated governance (fail-closed)
Given:
- `user_text`
- optional `evidence` (strings)

The pipeline computes an evidence score and routes each request into one of:

- **FREE** → allow full response
- **DAMPEN** → allow response but with higher “caution”
- **PROJECT** → do not answer; instead return:
  - **Q** (ask clarification) if the request is ambiguous
  - **U** (unknown / insufficient evidence) if evidence is missing

### ✅ 2) Action Gateway (Plan → Monitor → Policy)
Before calling the provider/LLM, the system runs a lightweight “action-risk” gate:

1. **Planner**: creates a minimal `ActionPlan` from the user text  
2. **Behavior Monitor**: assigns risk flags (e.g., `external_send`, `sensitive_data`, `writes_state`)  
3. **Policy Engine**: converts flags into a decision:
   - allow
   - block
   - (optional) require human approval

This is a **fail-closed** gate: if the policy blocks, the provider is not called.

### ✅ 3) Smoke tests / scenarios
Includes a small scenario runner that demonstrates:
- benign request with evidence → allowed
- exfil attempt (e.g., “send my API key…”) → blocked
- vague request with no evidence → PROJECT (U/Q)
- state-change request → blocked

---

## What the project does NOT do (yet)

### ❌ No real model introspection
- No logits, hidden states, or real attention weights from a real model.
- The `toy_attention` module uses random keys/values to visualize the effect of damping, but it is **not connected** to an LLM.

### ❌ No tool execution sandbox
- The policy gate is heuristic and string-based (for now).  
- There is no real tool runtime with permission scopes, audit logs, or external connectors.

### ❌ Not a production safety system
This is a prototype for learning + demonstration. It is not a substitute for a real safety framework, threat modeling, or security review.

---

## How it works (high level)





