from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from domain.project.types import Plan
from domain.utils.generate_api_key import generate_api_key
from domain.utils.generate_uuid import generate_uuid


@dataclass(frozen=True, slots=True)
class Project:
    project_id: UUID
    name: str
    plan: Plan
    api_key: str
    created_at: datetime

    @classmethod
    def create(cls, name: str, plan: Plan, env: str = "prod") -> "Project":
        return cls(
            project_id=generate_uuid(),
            name=name.strip(),
            plan=plan,
            api_key=generate_api_key(env),
            created_at=datetime.now(UTC),
        )
