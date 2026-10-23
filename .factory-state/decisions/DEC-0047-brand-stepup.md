# Decision Record

## Metadata

- Project: superstep
- Decision ID: DEC-0047
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-23
- Updated: 2026-10-23
- Related Architecture: DEC-0008 (UI conventions, theme tokens), DEC-0042 (channel brand logos)

## Context

The app showed a lucide `Workflow` glyph on stock shadcn neutral `--primary`, while the handbook used an off-system
violet (`#6c4bd8`) that collides with the LLM/Join node hues. The product is now called Superstep (LangGraph's
superstep: one execution step of the graph). The owner compared nine concepts and chose **D, "Step-up"**.

## Decision

1. **Mark:** a rounded square tile with an up-right arrow and a small "exponent" square (S², a step up). Assets in
   `frontend/public/brand/`: `superstep-mark(-dark).svg`, `superstep-mono.svg` (currentColor),
   `superstep-lockup(-dark|-mono).svg` and `superstep-wordmark.svg`. The wordmark is lower-case "superstep", Geist
   650, converted to outlines (no font dependency). Favicon SVG switches with `prefers-color-scheme`; PNG favicons
   (16/32), `apple-touch-icon.png`, 192/512 icons and `site.webmanifest`.
2. **In the app** the mark is the `Logo` / `LogoMark` component (`components/logo.tsx`), drawn with tokens only:
   tile `--primary`, arrow `--primary-foreground`, square `--brand-accent`; `mono` uses `currentColor`.
3. **Theme** (only these change; node and semantic colours untouched):

   | token | light | dark |
   |---|---|---|
   | `--primary` | `oklch(0.21 0.03 285)` | `oklch(0.93 0.012 285)` |
   | `--primary-foreground` | `oklch(0.985 0 0)` (17.0:1) | `oklch(0.21 0.03 285)` (14.5:1) |
   | `--ring` | `oklch(0.41 0.03 285)` | `oklch(0.7 0.02 285)` |
   | `--brand-accent` (+ `-foreground`) | `oklch(0.82 0.15 200)` | `oklch(0.55 0.12 215)` |

   `--sidebar-primary/-ring` follow `--primary/--ring`. The near-neutral primary is ≥ ΔE(OKLab) 0.20 from every
   node and semantic colour, so primary buttons never read as a node type or a status.
4. **`--brand-accent` is decorative** (logo, brand highlights). It is not a status colour and must not be used for
   node types.
5. **Handbook** uses the same mark and an ink + teal palette (`#171626`, links `#00728a` light / `#58e5ed` dark).

## Consequences

- One place to change the brand: `logo.tsx` + the tokens above. The old violet is gone from the repo.
