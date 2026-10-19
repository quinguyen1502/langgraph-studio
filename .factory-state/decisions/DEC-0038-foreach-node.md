# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0038
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-19
- Updated: 2026-10-19
- Related Requirements: REQ-0035
- Related Architecture: DEC-0009, DEC-0018
- Related Tasks: TASK-0049

## Context

The owner asked for a loop node. LangGraph offers two ways to repeat work: a cycle with a conditional edge, and `Send` fan-out (map-reduce). The studio already allows cycles through a Condition node. Side-effect nodes get idempotency keys and ledger entries per (run, node, iteration) (DEC-0018). Human pauses and job recovery restart the graph from saved state.

## Decision

1. **Node type `foreach`** with `items_field`, `item_field`, optional `index_field`, and `max_items` (default 100, 1–1000).
2. **Two labelled edges.** `each` leads into the body, which connects back to the For each node; `done` leaves the loop. The compiler adds a conditional edge with the mapping {each, done}.
3. **Sequential items on a LangGraph cycle.** Each visit reads the list, writes the next item (and index) and follows `each`; after the last item it follows `done`.
4. **Position in state.** The next index is kept in a state channel `loop:<node id>` that the compiler adds. Checkpoints, Human resume, and job recovery therefore carry it. It goes back to 0 at the end, so enclosing loops restart the list. Field names starting with `loop:` are reserved, and the run output leaves these keys out.
5. **Results through reducers.** The body collects results itself, for example with a list field that uses `append`. No new collection mechanism.
6. **Step budget.** The run's recursion limit is `STUDIO_RECURSION_LIMIT` plus, for each loop, `max_items × (body nodes + 1) + 1`, with nested loops multiplied. The total is capped at 100,000.
7. **Editor.** The first edge drawn from a For each node is labelled `each` and the second `done`. Its edges get a role picker in place of the free-text label.

## Rationale

- Sequential execution reuses the iteration counter, so every item gets its own idempotency key and ledger entry. Human pauses and recovery checkpoints also keep working.
- Parallel `Send` workers in one superstep would share an iteration number, so the ledger would return the first item's result for the others. They would also need private per-item state, which our checkpoints and trace do not model.

## Alternatives Considered

- Option: `Send` fan-out
  - Benefits: Items run in parallel
  - Tradeoffs: Per-item iteration keys, private item state in checkpoints and trace, and a join step after all items
  - Reason Not Chosen: Larger change. It can come later as a `parallel` option.
- Option: The node runs a saved workflow per item inside its own function
  - Benefits: Simple compile step
  - Tradeoffs: Inner nodes would vanish from the trace, and Human pauses and recovery would break inside
  - Reason Not Chosen: Hides the body

## Impacts

- Validator: For each rules; a cycle may pass through a Condition or a For each node; the parallel-writes check skips For each (one route at a time); the loop error now reads "Loop without a Condition or For each".
- Compiler: hidden loop channels, conditional edges. Runtime: larger recursion limit, run output without loop keys.
- Editor: new node colour tokens `--node-foreach*` (light and dark).

## Risks

- The trace and the paused-state view show the `loop:<id>` key. This is intended: it tells the author which item is next.

## Follow-Up

- Optional parallel mode with `Send` if the owner asks.
