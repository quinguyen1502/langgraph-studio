"""For each nodes (TASK-0049, DEC-0038): run a branch once per item of a list field, one item after another.

Edges: the `each` edge leads into the loop body, whose last node connects back to the For each node; the `done` edge
leaves the loop. Every visit takes the next item, writes it (and its 0-based index) to state and follows `each`; after
the last item it follows `done`. The body collects results itself, e.g. an LLM node writing to a list field with the
`append` reducer.

Items run one at a time, not in parallel, so Human pauses, recovery checkpoints, idempotency keys and the node ledger
work per item as in any other loop. The position is kept in state under `loop:<node id>`, so a resumed or recovered run
continues with the right item; it goes back to 0 when the loop finishes, so an enclosing loop starts the list again.
The list is read on every visit: a body that changes it changes what is left to do.
"""
from __future__ import annotations
from typing import Any, Callable, Dict, List

EACH, DONE = "each", "done"
PREFIX = "loop:"
MAX_ITEMS = (1, 1000)
DEFAULT_MAX = 100
BUDGET_CAP = 100_000  # LangGraph recursion limit ceiling for the extra For each steps


def cursor(nid: str) -> str: return PREFIX + nid


def visible(state: Dict[str, Any]) -> Dict[str, Any]:
    """State without the loop positions (the run's output)."""
    return {k: v for k, v in state.items() if not k.startswith(PREFIX)}


def max_items(d: Dict[str, Any]) -> int:
    v = d.get("max_items")
    return v if isinstance(v, int) and not isinstance(v, bool) else DEFAULT_MAX


def node_fn(node: Dict[str, Any]) -> Callable[[dict], dict]:
    nid, d = node["id"], node.get("data") or {}
    key, label, src = cursor(nid), d.get("label") or nid, d.get("items_field")

    def fn(state):
        items = state.get(src)
        if items is None: items = []
        if not isinstance(items, list):
            raise ValueError(f"For each '{label}' ({nid}): state.{src} must be a list (got {type(items).__name__})")
        if len(items) > (cap := max_items(d)):
            raise ValueError(f"For each '{label}' ({nid}): state.{src} has {len(items)} items, more than the limit of {cap}")
        i = state.get(key) or 0
        if i >= len(items): return {key: 0}  # finished: follow `done`
        out = {key: i + 1, d["item_field"]: items[i]}
        if d.get("index_field"): out[d["index_field"]] = i
        return out
    return fn


def router(nid: str) -> Callable[[dict], str]:
    key = cursor(nid)
    return lambda state: EACH if state.get(key) else DONE


def errors(nid: str, d: Dict[str, Any], out: List[dict], schema: List[dict], reaches: Callable[[str, str], bool]) -> List[str]:
    """Problems with one For each node. `reaches(a, b)`: b is reachable from a along edges."""
    errs: List[str] = []
    by = {f["name"]: f for f in schema}
    def field(key: str, what: str, types=None, required=True):
        name = d.get(key)
        if not name:
            if required: errs.append(f"For each node {nid}: choose the {what}")
            return
        f = by.get(name)
        if schema and f is None: errs.append(f"For each node {nid}: {what} '{name}' is not in the state"); return
        if f is None: return
        if types and f.get("type", "string") not in types: errs.append(f"For each node {nid}: {what} '{name}' must be of type {' or '.join(types)}")
        if key != "items_field" and (f.get("reducer") or "replace") != "replace":
            errs.append(f"For each node {nid}: {what} '{name}' must not have a reducer (each item replaces the last)")
    field("items_field", "list field", ("list",))
    field("item_field", "item field")
    field("index_field", "index field", ("integer", "number"), required=False)
    names = [d.get(k) for k in ("items_field", "item_field", "index_field") if d.get(k)]
    if len(set(names)) != len(names): errs.append(f"For each node {nid}: the list, item and index fields must be different fields")
    m = d.get("max_items")
    if m is not None and (isinstance(m, bool) or not isinstance(m, int) or not MAX_ITEMS[0] <= m <= MAX_ITEMS[1]):
        errs.append(f"For each node {nid}: max items must be an integer from {MAX_ITEMS[0]} to {MAX_ITEMS[1]}")
    labels = [e.get("label") for e in out]
    if sorted(labels) != [DONE, EACH]:
        errs.append(f"For each node {nid}: needs exactly one '{EACH}' edge (the loop body) and one '{DONE}' edge (after the last item)")
    else:
        body = next(e["target"] for e in out if e.get("label") == EACH)
        if not reaches(body, nid): errs.append(f"For each node {nid}: the '{EACH}' branch must lead back to this For each node")
    return errs


def step_budget(wf: Dict[str, Any]) -> int:
    """Extra LangGraph steps the For each loops of `wf` may need: max items × (body nodes + 1), nested loops multiplied.
    The body is every node reachable from the `each` target without passing the For each node (an upper bound)."""
    nodes = {n["id"]: n for n in wf.get("nodes", []) if isinstance(n, dict) and n.get("id")}
    loops = [i for i, n in nodes.items() if n.get("type") == "foreach"]
    if not loops: return 0
    out: Dict[str, List[dict]] = {}
    for e in wf.get("edges", []):
        if isinstance(e, dict) and e.get("source") in nodes and e.get("target") in nodes: out.setdefault(e["source"], []).append(e)
    memo: Dict[str, int] = {}

    def body(nid: str) -> List[str]:
        start = [e["target"] for e in out.get(nid, []) if e.get("label") == EACH]
        seen, stack = set(), list(start)
        while stack:
            x = stack.pop()
            if x == nid or x in seen: continue
            seen.add(x); stack += [e["target"] for e in out.get(x, [])]
        return list(seen)

    def cost(nid: str, active: frozenset) -> int:
        if nid in memo: return memo[nid]
        inner = sum(cost(b, active | {nid}) if nodes[b].get("type") == "foreach" and b not in active else 1 for b in body(nid))
        memo[nid] = min(BUDGET_CAP, max_items(nodes[nid].get("data") or {}) * (inner + 1) + 1)
        return memo[nid]
    return min(BUDGET_CAP, sum(cost(i, frozenset()) for i in loops))
