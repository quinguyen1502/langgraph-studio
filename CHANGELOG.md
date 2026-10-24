# Changelog

All notable changes to Superstep. Versions follow [Semantic Versioning](https://semver.org/); dates are in UTC+7.

## 0.5.0 (2026-10-24)

### Added

- **Web chat** (REQ-0048 phase 1). Backend: chat sessions and messages, a web chat trigger with Chat settings (input,
  reply and history fields, steps shown to visitors, turns and retention), Human nodes answered by the person chatting
  or by a reviewer (#116, migration `0035_chat_sessions`). Studio: a Chat side panel beside the canvas (Chat button or
  Shift+C, 340–760 px, fullscreen with the list of chats), a session picker and New chat, **View as** Workflow builder /
  Chat visitor with a preview banner, tool steps and confirmations in the thread (#117).
- **Editor layout**: the bottom panel is Run · Test · Code; Run shows the input and the logs side by side with a run
  picker and **View all**; Config folds away on narrow screens (#117).
- **Alignment guardrails** (TASK-0086, DEC-0055): rule 11 in `docs/ui-conventions.md`, `npm run lint:ui` on CI,
  `e2e/alignment.spec.ts`; Badge and TabsList `size="sm"`; ScrollArea content no longer overflows its panel (#118).
- **PaaS deploys**: an all-in-one image (UI, API and WebSocket on one port) with Render and Heroku buttons, Railway,
  Coolify and Dokploy configs (#119); Fly.io, DigitalOcean, Koyeb, Zeabur, Northflank and a self-hosted guide, image CI
  (#120); a remote sandbox service so Code nodes can run isolated where the platform has no Docker (#121).
  Guides in `docs/deploy/`.
- **Public demo mode** (`STUDIO_DEMO_MODE`): a shared read-only visitor with "Try the demo", seeded samples (the
  Chatbot with web chat on), Code, HTTP and Send email nodes off, mock models, a per-IP run limit and a demo banner;
  the live demo runs on Render (#122).

### Changed

- README restyled: centred header, overview screenshot, feature table; handbook screenshots and text refreshed for the
  new layout and the chat panel (#117).

### Earlier (0.4.0)

- TypeScript in Code mode on Deno and the LangGraph.js export shipped in 0.4.0 (#109–#112).
