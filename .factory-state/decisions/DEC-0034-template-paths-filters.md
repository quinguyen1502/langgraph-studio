# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0034
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-18
- Updated: 2026-10-18
- Related Requirements: REQ-0031
- Related Architecture:
- Related Tasks: TASK-0044

## Context

Node templates supported only `{{state.field}}`. Reading a nested value or reshaping it (case, a default, joining a list) needed an extra Tool node. The owner asked for paths and filters (remaining-work item 8).

## Decision

A reference is `{{ state.<field>[.<key>|.<index>]... [| <filter>[(<arg>)]]... }}`:

- The path walks dicts by key and lists by index. Any missing step gives `None`, which renders as an empty string.
- There is a fixed set of filters, applied left to right: `upper`, `lower`, `trim`, `json`, `length`, `first`, `last`, `default(text)`, `join(text)`, `truncate(number)`. An argument is one quoted string or an integer.
- One parser lives in `engine/templating.py`. The frontend copy is `lib/state-refs.ts`, and both read the cases in `backend/tests/fixtures/template_refs.json`.
- The validator checks every template field (LLM and Human prompt, HTTP URL and body, Retriever query, MCP argument strings) for the root field and for filter names and arguments. At run time, an invalid reference raises `TEMPLATE_REF_INVALID`.
- In the editor, references are atomic tags. Double-click turns a tag back into text until the cursor leaves it.

## Rationale

- A small closed set covers the common cases and cannot run code. There is no `eval`, and no template engine dependency.
- Keeping the existing `{{state.x}}` syntax means every saved workflow renders as before.

## Alternatives Considered

- Option: Jinja2 with a sandboxed environment
  - Benefits: Loops, conditions, a large filter set
  - Tradeoffs: A second template language beside the editor's tags, a sandbox to keep safe, and harder static checks
  - Reason Not Chosen: More than the requirement needs, and the editor could no longer show every reference as a tag
- Option: JSONPath / JMESPath for paths
  - Benefits: Standard syntax with filtering
  - Tradeoffs: A new dependency and a syntax the tags would have to render
  - Reason Not Chosen: A dotted path covers the requested cases

## Impacts

- A reference to a field that exists but holds `None` now renders as an empty string. Before, it rendered `null`.
- The Human prompt and HTTP URL and body are now checked on save. Before, only the LLM prompt, Retriever query, and MCP arguments were.

## Risks

- New filters must be added in both `templating.py` and `state-refs.ts`; the shared cases catch a parser mismatch but not a missing filter.

## Follow-Up

- None
