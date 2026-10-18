"""Node execution settings: retry and cache go to LangGraph, timeout caps the attempt."""
import time
from app.engine.compiler import compile_workflow
from app.engine.runtime import run_stream
from app.engine.tools import register_tool
from app.engine.validator import validate

def N(i, t, **d): return {"id": i, "type": t, "data": {"label": i, **d}}
def E(i, s, t): return {"id": i, "source": s, "target": t}
def wf(nodes, edges):
    return {"name": "t", "state": [{"name": "message", "type": "string"}, {"name": "out", "type": "string"}],
            "nodes": nodes, "edges": edges}

def tool(name, **data):
    return wf([N("s", "start"), N("t", "tool", mode="function", function=name, output_field="out", **data), N("e", "end")],
              [E("1", "s", "t"), E("2", "t", "e")])


_flaky = {"n": 0}

@register_tool("policy_flaky")
def _policy_flaky(state):
    _flaky["n"] += 1
    if _flaky["n"] < 3: raise ConnectionError("down")
    return "ok"


_hits = {"n": 0}

@register_tool("policy_count")
def _policy_count(state):
    _hits["n"] += 1
    return str(_hits["n"])


_sleeps = {"n": 0}

@register_tool("policy_sleep")
def _policy_sleep(state):
    _sleeps["n"] += 1
    time.sleep(0.6)
    return "slept"


def test_blank_settings_stay_valid_and_bad_ones_are_named():
    assert validate(tool("lookup_order")) == []
    bad = tool("lookup_order", retry={"max_attempts": 0}, timeout=0, cache_ttl=1.5)
    errs = validate(bad)
    assert any("retry attempts" in e for e in errs)
    assert any("timeout" in e for e in errs)
    assert any("cache TTL" in e for e in errs)


def test_retry_runs_the_node_again_after_a_connection_error():
    _flaky["n"] = 0
    out = compile_workflow(tool("policy_flaky", retry={"max_attempts": 3, "initial_interval": 0.01})).invoke({})
    assert out["out"] == "ok" and _flaky["n"] == 3


def test_cache_reuses_the_node_result_for_the_same_input():
    _hits["n"] = 0
    app = compile_workflow(tool("policy_count", cache_ttl=60))
    assert app.invoke({})["out"] == "1"
    assert app.invoke({})["out"] == "1"
    assert _hits["n"] == 1


def test_timeout_stops_the_attempt_and_retry_starts_another():
    _sleeps["n"] = 0
    started = time.perf_counter()
    evs = list(run_stream(tool("policy_sleep", timeout=0.15, retry={"max_attempts": 2, "initial_interval": 0.01}), {}))
    elapsed = time.perf_counter() - started
    err = evs[-1]
    assert err["type"] == "error" and err["node"] == "t"
    assert "timeout" in err["errors"][0].lower()
    assert _sleeps["n"] == 2
    assert elapsed < 0.8  # two capped attempts, not the 0.6s sleep twice


def test_retry_does_not_treat_a_human_pause_as_a_failure():
    w = wf([N("s", "start"), N("h", "human", prompt="ok?", output_field="out", retry={"max_attempts": 4, "initial_interval": 0.25}), N("e", "end")],
           [E("1", "s", "h"), E("2", "h", "e")])
    started = time.perf_counter()
    evs = list(run_stream(w, {}))
    assert evs[-1]["type"] == "run_waiting" and evs[-1]["node"] == "h"
    assert time.perf_counter() - started < 0.2
