Providers are pluggable.

- `EchoProvider` is the default (no API keys).
- To integrate a real model, add a new provider implementing:
  `answer(user_text: str, evidence: List[str], damping: float) -> LLMAnswer`
