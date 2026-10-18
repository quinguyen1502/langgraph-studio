from typing import Optional
from sqlalchemy import delete, or_, select
from ..models import McpServer
from ..models.database import Database


class McpServerRepository:
    def __init__(self, db: Database): self.db = db

    def visible(self, uid: str) -> list[McpServer]:
        """The user's own servers and every org server, org first then newest."""
        with self.db.session() as s:
            return list(s.scalars(select(McpServer).where(or_(McpServer.owner == uid, McpServer.scope == "org"))
                                  .order_by(McpServer.scope, McpServer.created.desc())))

    def get(self, sid: str) -> Optional[McpServer]:
        with self.db.session() as s: return s.get(McpServer, sid)

    def save(self, row: McpServer) -> McpServer:
        with self.db.session() as s: row = s.merge(row); s.commit(); return row

    def delete(self, sid: str) -> None:
        with self.db.session() as s: s.execute(delete(McpServer).where(McpServer.id == sid)); s.commit()
