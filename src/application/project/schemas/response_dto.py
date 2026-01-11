from datetime import datetime

from pydantic import BaseModel


class ProjectResponseDTO(BaseModel):
    project_id: str
    name: str
    plan: str
    api_key: str
    created_at: datetime
