import secrets
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from domain.exceptions.app import InvalidPayloadError
from domain.project.types import Plan
from domain.types import ProjectID
from domain.utils.generate_uuid import generate_uuid


class Project:
    __slots__ = ("_api_key", "_created_at", "_name", "_plan", "_project_id")

    def __init__(
        self,
        project_id: UUID,
        name: str,
        plan: Plan,
        api_key: str,
        created_at: datetime,
    ) -> None:
        self._project_id = project_id
        self._api_key = api_key
        self._created_at = created_at

        self.name = name
        self.plan = plan

    # --- FACTORY ---

    @classmethod
    def create(cls, name: str, plan: Plan, env: str = "prod") -> "Project":
        now = datetime.now(UTC)
        new_id = generate_uuid()
        random_part = secrets.token_urlsafe(32)
        new_api_key = f"wk_{env}_{random_part}"

        return cls(project_id=new_id, name=name, plan=plan, api_key=new_api_key, created_at=now)

    # --- GETTERS ---

    @property
    def project_id(self) -> ProjectID:
        return cast(ProjectID, self._project_id)

    @property
    def api_key(self) -> str:
        return self._api_key

    @property
    def created_at(self) -> datetime:
        return self._created_at

    # --- NAME ---

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        cleaned_name = value.strip()
        if len(cleaned_name) < 3:
            raise InvalidPayloadError("Project name must be at least 3 chars long.")
        if len(cleaned_name) > 100:
            raise InvalidPayloadError("Project name must be shorter than 100 chars.")

        self._name = value

    # PLAN

    @property
    def plan(self) -> Plan:
        return self._plan

    @plan.setter
    def plan(self, value: Plan | str) -> None:
        if isinstance(value, Plan):
            self._plan = value
        elif isinstance(value, str):
            try:
                self._plan = Plan(value)
            except ValueError as exc:
                raise InvalidPayloadError(f"Plan '{value}' is not valid.") from exc
        else:
            raise InvalidPayloadError("Invalid type for plan.")

    # --- MAGIC METHODS ---

    def __str__(self) -> str:
        return f"Project '{self.name}'"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} project_id={self._project_id} name={self._project_id}"
