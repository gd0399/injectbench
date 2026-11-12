"""Model access with cost metering, retries and a model-fallback chain.

`ModelChain("anthropic:claude-sonnet-5-5", fallbacks=["anthropic:claude-haiku-5-5"])`
tries the primary model with exponential backoff; when it keeps failing it moves
to the next model. Every call is metered (tokens, USD, latency) per agent.
"""
from __future__ import annotations

import random
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field

# USD per million tokens (input, output). List prices as of Nov 2026 — verify at
# https://platform.claude.com/docs/en/about-claude/pricing before publishing numbers.
# Haiku 5.5 is priced by prompt length; the <=100K-token tier is used here
# (agent prompts in this benchmark stay far below that).
PRICING: dict[str, tuple[float, float]] = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "offline": (0.0, 0.0),
}


def price(model: str, input_tokens: int, output_tokens: int) -> float:
    name = model.split(":", 1)[-1]
    if name not in PRICING:
        raise KeyError(f"no pricing for {name!r}; add it to agentbench.llm.PRICING")
    pin, pout = PRICING[name]
    return (input_tokens * pin + output_tokens * pout) / 1_000_000


@dataclass
class AgentUsage:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    seconds: float = 0.0


@dataclass
class UsageMeter:
    """Thread-safe usage accumulator for one task run."""
    budget_usd: float | None = None
    by_agent: dict[str, AgentUsage] = field(default_factory=lambda: defaultdict(AgentUsage))
    retries: int = 0
    model_fallbacks: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record(self, agent: str, model: str, in_tok: int, out_tok: int, seconds: float) -> None:
        with self._lock:
            u = self.by_agent[agent]
            u.calls += 1
            u.input_tokens += in_tok
            u.output_tokens += out_tok
            u.cost_usd += price(model, in_tok, out_tok)
            u.seconds += seconds

    def note_step(self, agent: str) -> None:
        """Offline backend: count a reasoning step with zero token usage."""
        with self._lock:
            self.by_agent[agent].calls += 1

    @property
    def cost_usd(self) -> float:
        return sum(u.cost_usd for u in self.by_agent.values())

    def totals(self) -> dict:
        t = AgentUsage()
        for u in self.by_agent.values():
            t.calls += u.calls
            t.input_tokens += u.input_tokens
            t.output_tokens += u.output_tokens
            t.cost_usd += u.cost_usd
            t.seconds += u.seconds
        return {"llm_calls": t.calls, "input_tokens": t.input_tokens, "output_tokens": t.output_tokens,
                "cost_usd": round(t.cost_usd, 6), "llm_seconds": round(t.seconds, 3),
                "retries": self.retries, "model_fallbacks": self.model_fallbacks,
                "by_agent": {k: vars(v) | {"cost_usd": round(v.cost_usd, 6)} for k, v in self.by_agent.items()}}

    def check_budget(self) -> None:
        if self.budget_usd is not None and self.cost_usd > self.budget_usd:
            raise BudgetExceeded(f"spent ${self.cost_usd:.4f} > budget ${self.budget_usd:.4f}")


class BudgetExceeded(RuntimeError):
    pass


def make_chat_model(spec: str, max_tokens: int = 4096, timeout: float = 120.0):
    """'anthropic:claude-sonnet-5-5' or 'openai:<model>' -> LangChain chat model."""
    provider, _, name = spec.partition(":")
    if not name:
        provider, name = "anthropic", provider
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        import os
        base = os.environ.get("AGENTBENCH_ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        return ChatAnthropic(model=name, max_tokens=max_tokens, timeout=timeout, max_retries=0,
                             base_url=base)
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=name, max_tokens=max_tokens, timeout=timeout, max_retries=0)
    raise ValueError(f"unknown provider {provider!r}")


class ModelChain:
    """Primary model + ordered fallbacks, each with retry/backoff on transient errors."""

    def __init__(self, primary: str, fallbacks: list[str] | None = None, retries: int = 2,
                 backoff: float = 1.5, factory=make_chat_model):
        self.specs = [primary, *(fallbacks or [])]
        self.retries = retries
        self.backoff = backoff
        self._factory = factory
        self._models: dict[str, object] = {}

    def _model(self, spec: str):
        if spec not in self._models:
            self._models[spec] = self._factory(spec)
        return self._models[spec]

    @property
    def name(self) -> str:
        return self.specs[0]

    def invoke(self, messages, *, tools=None, agent: str, meter: UsageMeter):
        last_exc: Exception | None = None
        for i, spec in enumerate(self.specs):
            model = self._model(spec)
            if tools:
                model = model.bind_tools(tools)
            for attempt in range(self.retries + 1):
                meter.check_budget()
                t0 = time.perf_counter()
                try:
                    msg = model.invoke(messages)
                except Exception as e:  # provider errors, timeouts, rate limits
                    last_exc = e
                    if getattr(e, "status_code", None) in (400, 401, 403, 404):
                        break               # not transient: retrying the same model won't help
                    if attempt < self.retries:
                        meter.retries += 1
                        time.sleep(self.backoff ** attempt + random.random() * 0.25)
                    continue
                um = getattr(msg, "usage_metadata", None) or {}
                meter.record(agent, spec, um.get("input_tokens", 0), um.get("output_tokens", 0),
                             time.perf_counter() - t0)
                if i > 0:
                    meter.model_fallbacks += 1
                return msg
        raise ModelUnavailable(f"all models failed for {agent}: {last_exc!r}") from last_exc


class ModelUnavailable(RuntimeError):
    pass
