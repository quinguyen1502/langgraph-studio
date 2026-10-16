from pydantic import BaseModel


class Finalize(BaseModel):
    graph_id: str
