"""Import a LangGraph repo (git URL or zip) as a read-only workflow."""
from ..core.errors import AppError
from ..engine import repo_import
from .workflow_service import WorkflowService

ZIP_MAX = 50 * 1024 * 1024


class ImportService:
    def __init__(self, workflows: WorkflowService): self.workflows = workflows

    def start(self, uid: str, url=None, branch=None, subdir=None, zip_bytes: bytes | None = None) -> dict:
        try:
            if zip_bytes is not None:
                if len(zip_bytes) > ZIP_MAX: raise AppError("IMPORT_ZIP_TOO_LARGE")
                jid = repo_import.start_job(uid, "zip", branch=None, subdir=subdir or None, zip_bytes=zip_bytes)
            elif url:
                jid = repo_import.start_job(uid, "url", url=url.strip(), branch=branch or None, subdir=subdir or None)
            else:
                raise AppError("IMPORT_SOURCE_REQUIRED")
        except repo_import.ImportError_ as e:
            raise AppError("IMPORT_INVALID", reason=str(e))
        return {"job_id": jid}

    def job(self, jid: str, uid: str) -> dict:
        j = repo_import.JOBS.get(jid)
        if not j or j["owner"] != uid: raise AppError("IMPORT_JOB_NOT_FOUND")
        return j

    def status(self, jid: str, uid: str) -> dict:
        return repo_import.public_job(self.job(jid, uid))

    def finalize(self, jid: str, graph_id: str, uid: str) -> dict:
        j = self.job(jid, uid)
        if j["status"] != "ready" or graph_id not in [g["id"] for g in j["graphs"]]:
            raise AppError("IMPORT_NOT_READY")
        return {"id": self.workflows.create(repo_import.to_workflow(j, graph_id), uid)}
