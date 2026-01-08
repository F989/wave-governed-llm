# Copilot / AI Agent Instructions for wave_governed_llm

Purpose: short, actionable guidance so an AI coding agent can be immediately productive in this repo.

Architecture (big picture)
- `app.py`: demo runner — shows example inputs, masks and calls `pipeline.run_case`.
- `pipeline.py`: orchestration for one governance+attention+LLM pass; returns `RunResult` dataclass.
- `wave_governor.py`: governance decision logic. Modes: `FREE`, `DAMPEN`, `PROJECT`. Key function: `decide(user_text, rho_energy)`.
- `toy_attention.py`: toy `governed_attention(query, keys, values, damping)` implementation (returns `output, weights, scores`).
- `wave_metrics.py`: helper metrics (e.g., `rho_energy`, `entropy`, `max_weight`, `l2`, `softmax`).
- `providers/`: provider implementations. `providers/dummy_llm.py` shows the expected provider API (`DummyLLM.answer(user_text, evidence, damping) -> LLMAnswer`).

Critical flows & why
- High-level flow in `pipeline.run_case`: build signal `C`, compute absorber `A` and `rho_energy`, call `decide` to choose governance mode, then either:
  - `PROJECT`: fail-closed — do not call LLM; return `message`, `state`, and `missing` (these messages are localized in the current code).
  - otherwise: call `governed_attention` (damping applied) and then call the provider's `answer` to generate text.
- This separation keeps governance decisions independent from LLM providers; any provider must be called only after `decide` permits it.

Project-specific conventions
- Determinism: `pipeline.run_case` accepts a `seed` and sets `np.random.seed(seed)` — preserve or expose this when adding tests.
- Governance thresholds are explicit: `t_dampen` and `t_project` parameters are used by `governor.decide` — prefer tuning those constants rather than scattering logic.
- `PROJECT` mode returns Hebrew user-facing messages in `wave_governor.py` — be careful when changing wording or localization.
- Provider API shape: implement an `answer(user_text: str, evidence: List[str], damping: float)` returning an object with `text` and `citations` (see `providers/dummy_llm.py`).

Integration points and replacements
- To replace the dummy model, add a concrete provider under `providers/` with the same `answer` signature and update `pipeline.py` where `DummyLLM()` is instantiated (or refactor to factory injection).
- Metrics and observability: `pipeline` returns `metrics` including `rho_energy`, `attention`, and `interference`. Use those fields when adding telemetry or unit tests.

Developer workflows (how to run / debug)
- Follow `README.md` quick-start for Windows PowerShell:
  - `python -m venv .venv`
  - `.\.venv\Scripts\Activate.ps1`
  - `pip install -r requirements.txt` (update file when adding deps)
  - `python app.py` runs the demo cases.
- Debugging tips: call `pipeline.run_case(...)` from a REPL or small script to reproduce a scenario; set `seed` for deterministic runs.

Testing and additions
- No tests are present. When adding tests, target `pipeline.run_case` behavior and governance branches (`FREE`, `DAMPEN`, `PROJECT`). Use explicit seeds and compare `RunResult` fields.

Editing rules for AI agents (do not change these without explicit human approval)
- Do not bypass `wave_governor.decide()` — governance must run before calling any LLM provider.
- Preserve the `RunResult` shape (decision, metrics, output) to avoid breaking consumers like `app.py`.
- If adding a real provider, keep the provider isolated under `providers/` and add minimal integration code; avoid inlining network calls into `pipeline.py`.

Where to look for examples
- Governance examples: [wave_governor.py](wave_governor.py)
- Orchestration & result shape: [pipeline.py](pipeline.py)
- Provider stub: [providers/dummy_llm.py](providers/dummy_llm.py)
- Demo runner: [app.py](app.py)

If anything here is unclear or you want more detail (extra examples, unit-test templates, or a provider scaffold), tell me which area to expand.
