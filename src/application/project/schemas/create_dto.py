from pydantic import BaseModel, Field

from domain.project.types import Plan


class CreateProjectDTO(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    plan: Plan = Field(default=Plan.FREE)
