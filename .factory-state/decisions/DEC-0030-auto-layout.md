# Decision

## Metadata

- Decision ID: DEC-0030
- Status: Accepted (implementation in review)
- Date: 2026-10-17
- Related: TASK-0027, REQ-0017, DEC-0027, PLAN-0001

## Decisions
- **dagre** (already a dependency, used for imported graphs) in a pure `lib/layout.ts` (`layoutGraph`, `overlaps`) with vitest tests. The old inline `autoLayout` in the editor was removed; imported graphs that need a layout use the same function.
- **Real sizes:** each node uses its measured React Flow size (fallback 200×70), so large nodes don't overlap and nodes in the same rank are centred.
- **Directions:** left→right (default) and top→bottom. The choice is remembered per browser (`localStorage lgs.layoutDir`). The button applies the remembered direction; the dropdown applies and remembers a new one.
- **Anchored:** the result keeps the graph's current top-left, so the canvas doesn't jump; the view then fits.
- **One undo step:** a single `setNodes` (DEC-0027 records it as one step). Whole graph only, with no "layout selection" (KISS). Edges are not re-routed (React Flow draws them).
- **Key:** Shift+L (registry, cheat sheet, palette); editors only, not for imported read-only graphs.
