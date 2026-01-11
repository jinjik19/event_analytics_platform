from domain.exceptions import EntityNotFoundError, InvalidError


class ProjectNotFoundError(EntityNotFoundError):
    pass


class InvalidProjectNameError(InvalidError):
    pass


class InvalidProjectPlanError(InvalidError):
    pass
