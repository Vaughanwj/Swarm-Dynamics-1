"""AgentRuntimePort backed by Claude on the standard Messages API (no batch): Haiku 5.5 by default, and
Sonnet 5.5 for the run 11 model pilot. Sonnet 5.5 needs nothing different here: it rejects
`thinking: disabled` and forced tool choice, and this adapter sends neither.

API details verified against the claude-api reference on 2026-10-19:
- Effort is `output_config.effort` (low, medium, high, xhigh, max). Haiku 5.5's default is
  `medium`. We always send it explicitly, pinned by config.
- Haiku 5.5 rejects non-default sampling parameters with a 400. `temperature`, `top_p` and `top_k`
  are never sent. The run manifest records this, and variance comes from replication.
- Adaptive thinking is on by default, so a response can begin with `thinking` blocks. Text is read
  by block type, and thinking counts toward max_tokens.
- Structured outputs: `output_config.format = {"type": "json_schema", "schema": ...}`. The engine
  still validates every answer itself.
- Prompt caching: the static rules block (system prompt) carries `cache_control: ephemeral`. The
  minimum cacheable prefix on Haiku 5.5 is 512 tokens, and the rules block is well above it.
- Two rate cards, split at 100K prompt tokens (cost.py). The brief keeps every prompt under that
  line. Prompts are estimated before sending and refused above `max_prompt_tokens`. Near misses and
  any measured overshoot are logged.
"""

from __future__ import annotations

import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Sequence

from .. import cost
from ..domain.views import AgentContext
from ..ports import Reply
from . import prompting

CACHE_WARM_SECONDS = 240  # the 5-minute cache: treat the prefix as cold after this long


class BudgetExceeded(RuntimeError):
    pass


class AnthropicHaikuAdapter:
    def __init__(
        self,
        system_text: str,
        log: Any,
        model: str = "claude-haiku-5-5",
        effort: str = "medium",
        max_tokens: int = 16000,
        concurrency: int = 10,
        timeout: float = 180.0,
        max_retries: int = 4,
        attempts: int = 2,
        workspace_id: str | None = None,
        budget_usd: float | None = None,
        prices: dict | None = None,
        chars_per_token: float = 2.0,  # for the pre-send size check: errs high (Milestone 2 measured 2.0 to 2.4)
        max_prompt_tokens: int = 95_000,
        near_miss_tokens: int = 80_000,
        log_prompts: bool = False,
        client: Any = None,
    ) -> None:
        if client is None:
            import anthropic  # imported lazily: mock runs need no SDK

            workspace_id = workspace_id or os.environ.get("ANTHROPIC_WORKSPACE_ID")
            headers = {"anthropic-workspace-id": workspace_id} if workspace_id else None
            client = anthropic.Anthropic(timeout=timeout, max_retries=max_retries, default_headers=headers)
        self.client = client
        self.system_text = system_text
        self.log = log
        self.model = model
        self.effort = effort
        self.max_tokens = max_tokens
        self.concurrency = concurrency
        self.attempts = attempts
        self.budget_usd = budget_usd
        self.price = cost.price_for(prices or {}, model)
        self.chars_per_token = chars_per_token
        self.max_prompt_tokens = max_prompt_tokens
        self.near_miss_tokens = near_miss_tokens
        self.log_prompts = log_prompts
        self.spent_usd = 0.0
        self._lock = threading.Lock()
        self._last_call = -1e9

    def manifest(self) -> dict[str, Any]:
        try:
            import anthropic
            sdk = anthropic.__version__
        except Exception:  # pragma: no cover - only when the SDK is missing
            sdk = None
        return {"runtime": "anthropic", "model": self.model, "effort": self.effort, "max_tokens": self.max_tokens,
                "temperature": "not sent: Claude Haiku 5.5 and Sonnet 5.5 return 400 on non-default sampling parameters",
                "thinking": "adaptive (model default, not sent)", "batch": False, "sdk_version": sdk,
                "prompt_caching": "system block, ephemeral", "budget_usd": self.budget_usd}

    def decide_batch(self, contexts: Sequence[AgentContext]) -> list[Reply]:
        if len(contexts) <= 1 or self.concurrency <= 1:
            return [self.decide(c) for c in contexts]
        out: list[Reply] = []
        rest = list(contexts)
        if time.monotonic() - self._last_call > CACHE_WARM_SECONDS:
            out.append(self.decide(rest.pop(0)))  # write the cache once, so the others read it
        with ThreadPoolExecutor(max_workers=min(self.concurrency, len(rest))) as pool:
            out.extend(pool.map(self.decide, rest))
        return out

    def decide(self, ctx: AgentContext) -> Reply:
        import anthropic

        user_text = prompting.user_prompt(ctx)
        schema = prompting.schema(ctx)
        est = int((len(self.system_text) + len(user_text) + len(json.dumps(schema))) / self.chars_per_token)
        if est > self.max_prompt_tokens:
            self.log.record("prompt_over_limit", round=ctx.round, agent=ctx.agent_id, estimated_tokens=est,
                            limit=self.max_prompt_tokens)
            return Reply(ctx.agent_id, fallback=True, error=f"prompt estimated at {est} tokens, over the limit")
        if est > self.near_miss_tokens:
            self.log.record("prompt_near_limit", round=ctx.round, agent=ctx.agent_id, estimated_tokens=est)

        last_error = None
        for attempt in range(1, self.attempts + 1):
            if self.budget_usd is not None and self.spent_usd >= self.budget_usd:
                raise BudgetExceeded(f"spent ${self.spent_usd:.4f} of a ${self.budget_usd:.2f} budget")
            started = time.monotonic()
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=[{"type": "text", "text": self.system_text, "cache_control": {"type": "ephemeral"}}],
                    messages=[{"role": "user", "content": user_text}],
                    output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": schema}},
                )
            except (anthropic.AuthenticationError, anthropic.PermissionDeniedError,
                    anthropic.NotFoundError, anthropic.BadRequestError):
                raise  # configuration problems: stop the run rather than fill it with fallbacks
            except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError) as e:
                last_error = f"{type(e).__name__}: {e}"
                self._log_call(ctx, attempt, started, user_text, error=last_error)
                continue
            finally:
                self._last_call = time.monotonic()
            usage = self._log_call(ctx, attempt, started, user_text, response=response)
            if response.stop_reason in ("refusal", "max_tokens"):
                last_error = f"stop_reason {response.stop_reason}"
                continue
            text = next((b.text for b in response.content if getattr(b, "type", None) == "text"), None)
            try:
                raw = json.loads(text or "")
            except json.JSONDecodeError as e:
                last_error = f"invalid JSON: {e}"
                self.log.record("parse_error", round=ctx.round, agent=ctx.agent_id, error=str(e), text=(text or "")[:2000])
                continue
            return Reply(ctx.agent_id, raw=raw, usage=usage)
        return Reply(ctx.agent_id, fallback=True, error=last_error)

    def _log_call(self, ctx: AgentContext, attempt: int, started: float, user_text: str,
                  response: Any = None, error: str | None = None) -> dict[str, Any]:
        row: dict[str, Any] = {
            "agent": ctx.agent_id, "kind": ctx.kind, "model": self.model, "effort": self.effort, "attempt": attempt,
            "latency_s": round(time.monotonic() - started, 3), "user_chars": len(user_text),
            "system_chars": len(self.system_text),
        }
        if self.log_prompts:
            row["user_text"] = user_text
        usage: dict[str, Any] = {}
        if response is not None:
            u = response.usage
            usage = {
                "input_tokens": u.input_tokens,
                "output_tokens": u.output_tokens,
                "cache_creation_input_tokens": getattr(u, "cache_creation_input_tokens", 0) or 0,
                "cache_read_input_tokens": getattr(u, "cache_read_input_tokens", 0) or 0,
            }
            row.update(usage, stop_reason=response.stop_reason, request_id=getattr(response, "_request_id", None))
            usd = cost.call_cost(row, self.price)
            with self._lock:
                self.spent_usd += usd
                row["usd"] = round(usd, 6)
                row["spent_usd"] = round(self.spent_usd, 6)
            if cost.prompt_tokens(row) > cost.PRICE_LINE:
                self.log.record("prompt_over_price_line", round=ctx.round, agent=ctx.agent_id,
                                prompt_tokens=cost.prompt_tokens(row))
        if error:
            row["error"] = error
        self.log.record("llm_call", round=ctx.round, **row)
        return usage
