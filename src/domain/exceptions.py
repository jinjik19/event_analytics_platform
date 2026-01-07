class DomainError(Exception):
    """Base class for all business exceptions."""

    pass


class EntityNotFoundError(DomainError):
    pass


class InvalidError(DomainError):
    pass
