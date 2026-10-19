# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0039
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-19
- Updated: 2026-10-19
- Related Requirements: REQ-0036
- Related Architecture: DEC-0032 (provider registry), DEC-0018 (effectively-once), DEC-0009
- Related Tasks: TASK-0050

## Context

TypeSafe's Jev takes a `state` and typed `questions` and returns typed `answers` with probabilities and confidence at `POST https://api.typesafe.ai/v1/systemone`. Pricing is input tokens only. The studio's providers are chat models used by LLM nodes and embeddings.

## Decision

1. **Credential through the provider registry.** `TypeSafe` is a `Provider` with `kind = "decision"`, no tools, no embeddings, and no chat. It reuses credential storage, encryption, **Test connection**, and HTTP error mapping. `kind` is in `/api/providers`, and the LLM node's credential list leaves out decision credentials. Test connection sends one tiny `noul` question, because there is no model list endpoint.
2. **A node type `decision`** (`engine/decisions.py`).
   - Data: `credential_id`, `model` (`jev-latest`), `text` (a template; an exact reference keeps its type, as for MCP arguments), `questions`, `output_field`.
   - Questions are stored editor-friendly: `options: [{label, description}]` for choice and `levels: [text]` for score. They are converted to the API's criteria when the request is built.
3. **Answers to state.**
   - A question's `field` gets the main value: the choice label, the score number, or the noul number. A Condition can branch on it.
   - `output_field` gets the full answers object.
4. **Same fallbacks as LLM nodes.** A credential, else `TYPESAFE_API_KEY` (and `TYPESAFE_BASE_URL`), else a deterministic offline mock, so flows can be built and tested without a key.
5. **Side-effect node.** `decision` is in `SIDE_EFFECT_TYPES`, so a recovered run reuses stored answers instead of paying again. It also accepts retry, timeout, and cache settings.
6. **Usage** is recorded as provider `typesafe` with the served model version. The price table has `jev`: $0.042 per million input tokens, output free.

## Rationale

- One HTTP call needs no SDK. The provider layer already gives safe error codes and keeps keys out of events.
- Writing the main value to a plain field reuses the existing Condition node, so no new routing feature is needed.

## Alternatives Considered

- Option: Use `typesafe-sdk`
  - Benefits: Retries and zstd compression built in
  - Tradeoffs: A new dependency for one endpoint. Retries already exist as node settings.
  - Reason Not Chosen: Not needed
- Option: Jev as an LLM provider
  - Benefits: No new node
  - Tradeoffs: Jev does not take a prompt or return text
  - Reason Not Chosen: Wrong shape
- Option: A Condition that reads nested paths (`answers.intent.choice`)
  - Benefits: No per-question field
  - Tradeoffs: Changes Condition semantics for every workflow
  - Reason Not Chosen: Larger change. Per-question fields are explicit.

## Impacts

- Provider info gains `kind`. `streaming` is false for TypeSafe.
- Validator: Decision rules. The parallel-writes check now counts every field a node writes (`written()`): LLM-style output fields, Decision fields, and For each item and index fields.
- Editor: a `decision-settings` component and node colour tokens `--node-decision*`.

## Risks

- The API was built from the docs, not tested against the live service (early access). The request and response shapes follow the documented examples. A mismatch shows up as `PROVIDER_BAD_RESPONSE` with the reason.

## Follow-Up

- `box` questions and images, if the owner needs them.
- Optional confidence threshold routing.
