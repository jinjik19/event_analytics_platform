from pydantic import BaseModel, Field, field_validator

from domain.project.types import Plan


class CreateProjectDTO(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    plan: Plan = Field(default=Plan.FREE)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()
