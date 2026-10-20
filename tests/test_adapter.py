"""The Haiku 5.5 adapter against a fake client: no API calls, no spend."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from swarm_village.adapters.anthropic_haiku import AnthropicHaikuAdapter, BudgetExceeded
from swarm_village.adapters.storage import MemoryEventLog
from swarm_village.domain.actions import parse

from .helpers import answer, step, village


def response(text: str, stop: str = "end_turn", inp: int = 3000, out: int = 400, cache_read: int = 0):
    content = [SimpleNamespace(type="thinking", thinking="", signature="sig"), SimpleNamespace(type="text", text=text)]
    usage = SimpleNamespace(input_tokens=inp, output_tokens=out, cache_creation_input_tokens=0,
                            cache_read_input_tokens=cache_read)
    return SimpleNamespace(content=content, stop_reason=stop, usage=usage, _request_id="req_1")


class FakeClient:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls: list[dict] = []
        self.messages = SimpleNamespace(create=self.create)

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.replies.pop(0)


def adapter(replies, **kw):
    log = MemoryEventLog()
    client = FakeClient(replies)
    return AnthropicHaikuAdapter("SYSTEM RULES", log, client=client, **kw), client, log


def context():
    return step(village())[0]


def test_request_shape_matches_haiku_5_5():
    a, client, log = adapter([response(json.dumps(answer()))])
    reply = a.decide(context())
    call = client.calls[0]
    assert call["model"] == "claude-haiku-5-5"
    assert call["output_config"]["effort"] == "medium"
    assert call["output_config"]["format"]["type"] == "json_schema"
    assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
    for banned in ("temperature", "top_p", "top_k", "thinking"):
        assert banned not in call
    assert call["messages"][-1]["role"] == "user"  # no prefill
    assert reply.raw == answer() and not reply.fallback
    row = next(e for e in log.events if e["type"] == "llm_call")
    assert row["input_tokens"] == 3000 and row["usd"] == pytest.approx((3000 * 0.10 + 400 * 0.50) / 1e6)


def test_text_is_read_by_block_type_after_thinking_blocks():
    a, _, _ = adapter([response(json.dumps(answer(eat=3)))])
    assert a.decide(context()).raw["eat"] == 3


def test_truncated_or_unparseable_answers_retry_then_fall_back():
    a, client, log = adapter([response("{", stop="max_tokens"), response("not json")])
    reply = a.decide(context())
    assert reply.fallback and len(client.calls) == 2
    assert any(e["type"] == "parse_error" for e in log.events)


def test_oversized_prompts_are_refused_before_any_call():
    a, client, log = adapter([], max_prompt_tokens=100)
    reply = a.decide(context())
    assert reply.fallback and not client.calls
    assert any(e["type"] == "prompt_over_limit" for e in log.events)


def test_prompts_over_the_price_line_are_flagged_and_priced_at_the_long_rate():
    a, _, log = adapter([response(json.dumps(answer()), inp=120_000)])
    a.decide(context())
    assert any(e["type"] == "prompt_over_price_line" for e in log.events)
    row = next(e for e in log.events if e["type"] == "llm_call")
    assert row["usd"] == pytest.approx((120_000 * 0.50 + 400 * 2.50) / 1e6)


def test_budget_stops_the_run():
    a, _, _ = adapter([response(json.dumps(answer()), inp=1_000_000)], budget_usd=0.05)
    a.decide(context())
    with pytest.raises(BudgetExceeded):
        a.decide(context())


def test_the_engine_validates_whatever_the_model_returns():
    a, _, _ = adapter([response(json.dumps({"actions": [{"type": "steal", "to": "a02"}], "extra": 1}))])
    reply = a.decide(context())
    d = parse(reply.raw, ("work", "read", "message", "post", "note", "press_button"), 600)
    assert not d.actions and len(d.errors) == 2


def test_manifest_records_that_temperature_is_not_sent():
    a, _, _ = adapter([])
    m = a.manifest()
    assert m["model"] == "claude-haiku-5-5" and m["effort"] == "medium" and "not sent" in m["temperature"]
    assert m["batch"] is False


def test_against_the_real_sdk_over_a_mock_transport():
    """The real SDK builds and parses the request; a mock transport stands in for the network."""
    anthropic = pytest.importorskip("anthropic")
    import inspect

    from anthropic.resources.messages import Messages

    try:  # the 1.x SDK runs on httpx2; older ones on httpx
        import httpx2 as httpx
    except ImportError:
        import httpx

    if "output_config" not in inspect.signature(Messages.create).parameters:
        pytest.skip(f"anthropic {anthropic.__version__} predates output_config; the image pins >=1.13")
    sent = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content))
        return httpx.Response(200, json={
            "id": "msg_1", "type": "message", "role": "assistant", "model": "claude-haiku-5-5",
            "content": [{"type": "thinking", "thinking": "", "signature": "sig"},
                        {"type": "text", "text": json.dumps(answer(eat=2))}],
            "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": 1200, "output_tokens": 300, "cache_creation_input_tokens": 0,
                      "cache_read_input_tokens": 900},
        })

    client = anthropic.Anthropic(api_key="test-not-a-real-key", base_url="http://test.invalid",
                                 http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    log = MemoryEventLog()
    a = AnthropicHaikuAdapter("SYSTEM RULES " * 200, log, client=client)
    reply = a.decide(context())
    assert reply.raw["eat"] == 2 and reply.usage["cache_read_input_tokens"] == 900
    body = sent[0]
    assert body["model"] == "claude-haiku-5-5" and body["output_config"]["effort"] == "medium"
    assert body["output_config"]["format"]["type"] == "json_schema"
    assert body["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert not {"temperature", "top_p", "top_k", "thinking"} & set(body)
