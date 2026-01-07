import secrets
from datetime import datetime

from uuid6 import uuid7

from domain.project.types import Plan


class Project:
    def __init__(self, name: str, plan: Plan, env: str) -> None:
        self._project_id = uuid7()
        self.name = name
        self.plan = plan
        self._api_key = self._generate_api_key(env)
        self.created_at = datetime.now()

    # --- GETTERS ---
    @property
    def project_id(self) -> str:
        return self._project_id

    @property
    def name(self) -> str:
        return self.name

    @property
    def plan(self) -> Plan:
        return self.plan

    @property
    def api_key(self) -> str:
        return self._api_key

    # --- SETTERS ---

    @name.setter
    def name(self, value: str) -> None:
        cleaned_name = value.strip()
        if len(cleaned_name) < 3:
            # TODO: Replace with proper exception
            raise ValueError("Project name must be at least 3 chars long.")
        if len(value) > 100:
            # TODO: Replace with proper exception
            raise ValueError("Project name must be shorter than 100 chars.")

        self.name = value

    @plan.setter
    def plan(self, value: Plan) -> None:
        if not isinstance(value, Plan):
            raise ValueError("Invalid plan type.")

        self.plan = value

    # --- LOGIC ---

    def _generate_api_key(self, env: str) -> str:
        """Genereate api key for project use env.

        Attrs:
            env: Current environment

        """
        random_part = secrets.token_urlsafe(32)
        return f"ak_{env}_{random_part}"

    # --- MAGIC METHODS ---

    def __str__(self) -> str:
        return f"Project '{self.name}'"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} project_id={self._project_id} name={self._project_id}"
