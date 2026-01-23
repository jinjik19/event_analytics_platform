from collections.abc import Mapping
from typing import Any

from fastapi import status

from domain.exceptions.base import BaseError


EXCEPTION_TO_STATUS_CODE = {
    "UnexpectedError": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "InvalidPayloadError": status.HTTP_400_BAD_REQUEST,
    "NotFoundError": status.HTTP_404_NOT_FOUND,
    "UnauthorizedError": status.HTTP_401_UNAUTHORIZED,
    "ValidationError": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "RateLimitExceededError": status.HTTP_429_TOO_MANY_REQUESTS,
    "ForbiddenError": status.HTTP_403_FORBIDDEN,
}


def get_status_code(exc: "BaseError") -> int:
    if exc.code() in EXCEPTION_TO_STATUS_CODE:
        return EXCEPTION_TO_STATUS_CODE[exc.code()]

    for base in type(exc).__bases__:
        if base.__name__ in EXCEPTION_TO_STATUS_CODE:
            return EXCEPTION_TO_STATUS_CODE[base.__name__]

    raise Exception(f"No status found for {exc}")


def exception_schema(exceptions: list["BaseError"]) -> dict[int, dict[str, Any]]:
    responses: dict[int, dict[str, Any]] = {}

    for exc in exceptions:
        add_exception_to_schemas_dict(responses, exc)

    return responses


def add_exception_to_schemas_dict(schemas: dict[int, dict[str, Any]], exception: BaseError) -> None:
    status_code = get_status_code(exception)
    if status_code in schemas:
        schemas[status_code]["content"]["application/json"]["examples"].update(
            exception_to_example(exception)
        )
        return

    schemas.update(exception_to_response_schema(exception))


def exception_to_response_schema(exception: BaseError) -> dict[int, dict[str, Any]]:
    schema = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "title": "Error code",
            },
            "message": {
                "type": "string",
                "title": "Error description",
            },
            "payload": {
                "type": "object",
                "title": "Additional information",
            },
            "debug": {
                "type": "string",
                "title": "Traceback or other internal information",
            },
        },
    }
    status_code = get_status_code(exception)
    return {
        status_code: {
            "content": {
                "application/json": {
                    "schema": schema,
                    "examples": exception_to_example(exception),
                },
            },
        },
    }


def exception_to_example(exception: BaseError) -> dict[str, dict[str, Any]]:
    code = exception.code()
    return {
        code: {
            "value": {
                "code": code,
                "message": exception.message,
            },
        },
    }


class ApiError:
    def __init__(self, original_error: BaseError) -> None:
        self._original_error = original_error

    @property
    def status_code(self) -> int:
        return get_status_code(self._original_error)

    @property
    def code(self) -> str:
        return type(self._original_error).__name__

    def to_json(self) -> Mapping[str, Any]:
        return self._original_error.to_json()
