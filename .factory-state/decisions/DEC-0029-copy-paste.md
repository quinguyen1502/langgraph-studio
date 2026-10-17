# Decision

## Metadata

- Decision ID: DEC-0029
- Status: Accepted (implementation in review)
- Date: 2026-10-17
- Related: TASK-0026, REQ-0016, DEC-0026, DEC-0027, PLAN-0001

## Decisions
- **Pure functions** in `lib/clipboard.ts` (`copySelection`, `pasteClip`, `parseClip`) with vitest tests; the editor only wires keys and buttons.
- **Versioned payload** `{"format":"langgraph-studio/nodes","version":1,nodes,edges}` stored in `localStorage` (`lgs.clipboard`), so a selection can be pasted into another workflow or tab in the same browser. It is also written to the system clipboard as text (best effort) but paste reads only our store: reading the system clipboard needs a permission prompt and foreign text is never parsed as nodes.
- **What is copied:** selected nodes except Start/End, their settings without runtime `_` fields, and only edges whose two ends are both copied.
- **Paste:** fresh unique ids for nodes and edges; pasted elements become the selection. In the same workflow, each repeated paste is offset by another 40 px. In a different workflow, the group lands in the middle of the view.
- **Credentials:** a `credential_id` the user cannot use in this browser session (not in their credential list) is cleared and the toast says so. Other references (knowledge base, MCP server, channel, subgraph) are kept, because the server validates them on save and run.
- **Undo:** a paste, duplicate or cut is one state update, so it is one history step (DEC-0027).
- **Keys** (registry group `clipboard`): Mod+C, Mod+X, Mod+V, Mod+D (Duplicate, which overrides the browser's bookmark shortcut on the canvas only). Text fields and page text keep native copy/paste. Viewers can copy but not cut, paste or duplicate. The inspector also has a **Duplicate** button.

## Consequences
- The clipboard is per browser profile; there is no cross-device copy.
