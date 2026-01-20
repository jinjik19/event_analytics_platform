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


class RateLimitExceededError(BaseError):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after
        super().__init__(message=f"Rate limit exceeded. Retry after {retry_after} seconds.")
