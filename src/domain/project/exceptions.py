from domain.exceptions import EntityNotFoundError, InvalidError


class ProjectNotFoundError(EntityNotFoundError):
    def __init__(self, project_id: str) -> None:
        super().__init__(f"Project with id {project_id} not found")


class InvalidProjectNameError(InvalidError):
    pass


class InvalidProjectPlanError(InvalidError):
    pass
