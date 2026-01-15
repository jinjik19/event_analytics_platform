from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    message: str
    payload: Mapping[str, Any] | None = None
    debug: str | None = None


RESPONSE = {
    400: {"model": ErrorResponse, "description": "Invalid payload"},
    404: {"model": ErrorResponse, "description": "Not found"},
    422: {
        "model": ErrorResponse,
        "description": "Validation error",
    },
    500: {
        "model": ErrorResponse,
        "description": "Unexcepted error",
    },
}
