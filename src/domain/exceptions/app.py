from domain.exceptions.base import BaseError


class NotFoundError(BaseError):
    pass


class InvalidPayloadError(BaseError):
    pass


class UnauthorizedError(BaseError):
    pass


class UnexpectedError(BaseError):
    pass


class ValidationError(BaseError):
    pass
