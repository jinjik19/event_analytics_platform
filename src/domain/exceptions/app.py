from domain.exceptions.base import BaseError


class NotFoundError(BaseError):
    pass


class InvalidError(BaseError):
    pass


class UnauthorizedError(BaseError):
    pass
