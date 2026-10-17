# Decision

## Metadata

- Decision ID: DEC-0021
- Status: Accepted (implementation in review)
- Date: 2026-10-17
- Related: TASK-0012, REQ-0007, REQ-0008, ARCH-0001

## Context

REQ-0007 asks for knowledge bases (document upload, chunking, embeddings, vector store) and a Retriever node. The open question was the vector store, pgvector or Chroma. The owner approved (2026-10-17): pgvector on Postgres, a plain-table brute-force fallback on SQLite, a deterministic mock embedding offline, OpenAI `text-embedding-3-small` by default through the existing credentials, txt/md/pdf uploads up to 10 MB, a knowledge base management UI and a Retriever node.

## Decisions

### Store
- Tables `knowledge_bases`, `kb_documents`, `kb_chunks` (migration `0019_knowledge_bases`). Each knowledge base has one owner, like workflows and credentials.
- Postgres: the migration runs `CREATE EXTENSION IF NOT EXISTS vector` inside a savepoint. When that works, `kb_chunks.embedding` becomes an untyped `vector` column and search is `ORDER BY embedding <=> query` in SQL, filtered by knowledge base and vector dimension.
- When the extension is missing (plain Postgres image, no privilege) or on SQLite, the column stays JSON text and the repository ranks the knowledge base's chunks by cosine similarity in Python. Same API, same results; it is slower only for large knowledge bases.
- No ANN index (HNSW/IVFFlat). Those need a fixed dimension, and models differ (mock 512, `text-embedding-3-small` 1536). Search is always filtered to one knowledge base, so an exact scan is fine at this scale. An index per dimension can follow if needed.
- Compose image: `pgvector/pgvector:pg17`, not `pg16`. The stack already ran Postgres 17 (`postgres:17-alpine`). A pg16 image cannot open a pg17 data directory, so existing `pgdata` volumes would stop working. pg17 keeps the major version and adds the extension. Verified on the existing compose volume: it upgraded to `0019` with a `vector` column.

### Embeddings (`engine/embeddings.py`)
- Selection mirrors LLM calls. The knowledge base's credential (OpenAI-compatible, encrypted, resolved by the owner), else `OPENAI_API_KEY`, else the mock. Anthropic credentials are rejected (no embeddings API).
- Default model: `text-embedding-3-small`, editable per knowledge base. OpenAI requests are batched (96 inputs).
- Mock: a feature-hashed bag of stemmed words without stop words, L2-normalised, 512 dimensions. It is deterministic and offline, and texts that share content words rank higher. That is enough to exercise retrieval end to end, but it is not a semantic model.
- Each knowledge base records the effective `embedder` (`mock:512`, `openai:<model>`) of its stored vectors. If the effective embedder changes (a key added to the environment, a model or credential edited), search returns `KB_EMBEDDER_CHANGED` instead of comparing incompatible vectors. Editing the model or credential in the UI re-indexes automatically. Uploading into a knowledge base with a stale embedder re-indexes first. `POST …/reindex` re-embeds on demand.

### Documents (`engine/documents.py`)
- `.txt`, `.md` (UTF-8, or UTF-16) and `.pdf` (text layer via `pypdf`; scanned PDFs without text give `KB_FILE_EMPTY`). Max 10 MB, checked on the bytes read (`MAX_BYTES + 1`).
- Paragraph-aware chunks of up to 800 characters; longer paragraphs are cut at a word boundary with 120 characters of overlap.
- Ingestion is synchronous within the upload request. A document and its chunks are stored in one transaction.

### Retriever node
- `type: retriever`, `data`: `knowledge_base_id`, `query` (template, `{{state.field}}`), `top_k` (1–20, default 4), `output_field`. Output: a list of `{text, score, document_id, filename, index}`.
- The engine gets the search through a run-time port (`engine/ports.py`, `Ports.retrieve`), bound to the run's owner by `RunService.ports(uid)`. The engine never touches repositories. Another user's knowledge base fails the node with `KB_NOT_FOUND`.
- Validator: a knowledge base is required, `top_k` must be 1–20, query variables must be state fields; the node counts as a writer for the parallel-write rule.

### API and UI
- `GET/POST /api/knowledge-bases`, `GET/PUT/DELETE /api/knowledge-bases/{id}`, `POST /api/knowledge-bases/{id}/documents` (multipart `file`), `DELETE …/documents/{doc}`, `POST …/reindex`, `POST …/search` `{query, top_k}`.
- New error codes `KB_*` (catalog, `docs/api-errors.md`, en/vi).
- Settings → Knowledge bases: create, upload, document table, test search with scores, settings (model, key, re-index, delete). The editor has a Retriever palette item (new `--node-retriever` token) and a settings panel with a knowledge base picker, top-k and a link to manage knowledge bases.

## Consequences
- Plain-Postgres deployments keep working (fallback); pgvector only makes search faster.
- Knowledge bases are owner-only until RBAC/sharing (TASK-0014) decides otherwise.
