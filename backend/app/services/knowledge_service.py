"""Knowledge bases (TASK-0012): CRUD, document ingestion (extract → chunk → embed → store), search, and the
run-time `retriever(uid)` port used by Retriever nodes. Owner-only, like workflows and credentials."""
from __future__ import annotations
import os, time, uuid
from typing import Any, Callable, Optional
from ..core.errors import AppError
from ..engine import documents, embeddings
from ..engine.llm import LLMError
from ..models import KbDocument, KnowledgeBase
from ..repositories import KnowledgeRepository

MAX_BYTES = 10 * 1024 * 1024
NAME_MAX = 120
TOP_K_MAX = 20


def public(kb: KnowledgeBase, docs: int = 0, chunks: int = 0) -> dict:
    return {"id": kb.id, "name": kb.name, "description": kb.description, "model": kb.model or embeddings.DEFAULT_MODEL,
            "credential_id": kb.credential_id, "embedder": kb.embedder, "documents": docs, "chunks": chunks, "created": kb.created}


def public_doc(d: KbDocument) -> dict:
    return {"id": d.id, "filename": d.filename, "size": d.size, "chunks": d.chunks, "created": d.created}


class KnowledgeService:
    def __init__(self, repo: KnowledgeRepository, credentials=None):
        self.repo, self.credentials = repo, credentials

    # ---- knowledge bases ----
    def list(self, uid: str) -> list[dict]:
        return [public(kb, n, c) for kb, n, c in self.repo.list_for_owner(uid)]

    def _owned(self, kid: str, uid: str) -> KnowledgeBase:
        kb = self.repo.get_owned(kid, uid)
        if kb is None: raise AppError("KB_NOT_FOUND")
        return kb

    def get(self, kid: str, uid: str) -> dict:
        kb = self._owned(kid, uid); docs = self.repo.documents(kid)
        return {**public(kb, len(docs), sum(d.chunks for d in docs)), "files": [public_doc(d) for d in docs]}

    def _clean(self, uid: str, name: Optional[str], credential_id: Optional[str]) -> tuple[str, Optional[str]]:
        n = (name or "").strip()
        if not n: raise AppError("KB_NAME_REQUIRED")
        if len(n) > NAME_MAX: raise AppError("KB_NAME_TOO_LONG", max=NAME_MAX)
        cid = credential_id or None
        if cid and self.credentials is not None: self.credentials.resolve(uid, cid)  # CREDENTIAL_NOT_FOUND if not yours
        return n, cid

    def create(self, uid: str, name: str, description: str | None = None, model: str | None = None, credential_id: str | None = None) -> dict:
        n, cid = self._clean(uid, name, credential_id)
        kb = KnowledgeBase(id=uuid.uuid4().hex[:10], owner=uid, name=n, description=(description or "").strip() or None,
                           model=(model or "").strip() or embeddings.DEFAULT_MODEL, credential_id=cid, created=time.time())
        return public(self.repo.add(kb))

    def update(self, kid: str, uid: str, name: str, description: str | None = None, model: str | None = None,
               credential_id: str | None = None) -> dict:
        """Changing the model or credential re-embeds the stored chunks when they would no longer match."""
        kb = self._owned(kid, uid); n, cid = self._clean(uid, name, credential_id)
        self.repo.update(kid, name=n, description=(description or "").strip() or None, model=(model or "").strip() or embeddings.DEFAULT_MODEL,
                         credential_id=cid)
        kb = self._owned(kid, uid)
        if kb.embedder and kb.embedder != self._embedder_id(kb): self.reindex(kid, uid)
        return self.get(kid, uid)

    def delete(self, kid: str, uid: str) -> dict:
        self._owned(kid, uid); self.repo.delete(kid); return {"ok": True}

    # ---- embeddings ----
    def _cred(self, kb: KnowledgeBase) -> Optional[dict]:
        return self.credentials.resolve(kb.owner, kb.credential_id) if kb.credential_id and self.credentials is not None else None

    def _embedder_id(self, kb: KnowledgeBase) -> str:
        try: return embeddings.embedder_id(kb.model, self._cred(kb))
        except LLMError as e: raise AppError("KB_EMBEDDING_FAILED", reason=str(e)) from None

    def _embed(self, kb: KnowledgeBase, texts: list[str]) -> list[list[float]]:
        try: return embeddings.embed(texts, kb.model, self._cred(kb))
        except LLMError as e: raise AppError("KB_EMBEDDING_FAILED", reason=str(e)) from None

    # ---- documents ----
    def upload(self, kid: str, uid: str, filename: str, data: bytes) -> dict:
        kb = self._owned(kid, uid)
        name = os.path.basename(filename or "").strip() or "document.txt"
        if not name.lower().endswith(documents.EXTENSIONS): raise AppError("KB_FILE_TYPE_UNSUPPORTED", allowed=", ".join(documents.EXTENSIONS))
        if len(data) > MAX_BYTES: raise AppError("KB_FILE_TOO_LARGE", max_mb=MAX_BYTES // (1024 * 1024))
        try: text = documents.extract(name, data)
        except documents.DocumentError as e: raise AppError("KB_FILE_UNREADABLE", reason=str(e)) from None
        parts = documents.chunk(text)
        if not parts: raise AppError("KB_FILE_EMPTY")
        emb = self._embedder_id(kb)
        if kb.embedder and kb.embedder != emb: self.reindex(kid, uid)  # keep one embedder per knowledge base
        vectors = self._embed(kb, parts)
        doc = self.repo.add_document(KbDocument(id=uuid.uuid4().hex[:10], kb_id=kid, filename=name, size=len(data), chunks=len(parts),
                                                created=time.time()), parts, vectors)
        if kb.embedder != emb: self.repo.update(kid, embedder=emb)
        return public_doc(doc)

    def delete_document(self, kid: str, did: str, uid: str) -> dict:
        self._owned(kid, uid)
        if self.repo.get_document(kid, did) is None: raise AppError("KB_DOCUMENT_NOT_FOUND")
        self.repo.delete_document(did); return {"ok": True}

    def reindex(self, kid: str, uid: str) -> dict:
        """Re-embed every chunk with the knowledge base's current embedder (after a model/credential change)."""
        kb = self._owned(kid, uid); rows = self.repo.chunk_texts(kid)
        vectors = self._embed(kb, [t for _, t in rows]) if rows else []
        self.repo.set_embeddings([(i, v) for (i, _), v in zip(rows, vectors)])
        self.repo.update(kid, embedder=self._embedder_id(kb) if rows else None)
        return {"ok": True, "chunks": len(rows)}

    # ---- search ----
    def search(self, kid: str, uid: str, query: str, top_k: int = 4) -> list[dict[str, Any]]:
        kb = self._owned(kid, uid)
        q = (query or "").strip()
        if not q: raise AppError("KB_QUERY_REQUIRED")
        k = max(1, min(int(top_k or 4), TOP_K_MAX))
        if not kb.embedder: return []  # empty knowledge base
        if kb.embedder != self._embedder_id(kb): raise AppError("KB_EMBEDDER_CHANGED")
        return self.repo.search(kid, self._embed(kb, [q])[0], k)

    def retriever(self, uid: str) -> Callable[[str, str, int], list[dict]]:
        """Port for Retriever nodes, bound to the run's user (engine.ports.Ports.retrieve)."""
        return lambda kid, query, k: self.search(kid, uid, query, k)
