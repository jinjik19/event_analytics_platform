from typing import Any, cast

import structlog
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from pydantic import ValidationError
from starlette.types import ASGIApp, Receive, Scope, Send

from domain.exceptions.app import RateLimitExceededError, UnexpectedError
from domain.exceptions.app import ValidationError as ApiValidationError
from domain.exceptions.base import BaseError
from entrypoint.api.exceptions import ApiError


logger = structlog.get_logger("api")


class ExceptionHandlerMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            response = await self._get_response_for_exception(exc)
            await response(scope, receive, send)

    async def _get_response_for_exception(self, exc: Exception) -> ORJSONResponse:
        if isinstance(exc, BaseError):
            logger.error("Request failed with exception", extra={"error": exc})
            return self._app_exception_handler(exc)

        if isinstance(exc, (ValidationError, RequestValidationError)):
            logger.error("Request failed with exception", extra={"error": exc})
            return self._validation_exception_handler(exc)

        logger.error("Request failed with unexpected exception", extra={"error": exc})
        return self._base_exception_handler(exc)

    def _app_exception_handler(self, exc: BaseError) -> ORJSONResponse:
        error = ApiError(exc)
        headers: dict[str, str] | None = None

        if isinstance(exc, RateLimitExceededError):
            headers = {"Retry-After": str(exc.retry_after)}

        return ORJSONResponse(
            status_code=error.status_code,
            content=error.to_json(),
            headers=headers,
        )

    def _base_exception_handler(self, exc: Exception) -> ORJSONResponse:
        error = ApiError(UnexpectedError(debug=repr(exc)))
        return ORJSONResponse(
            status_code=error.status_code,
            content=error.to_json(),
        )

    def _validation_exception_handler(
        self, exc: ValidationError | RequestValidationError
    ) -> ORJSONResponse:
        errors = exc.errors() if hasattr(exc, "errors") else []
        payload = cast(list[dict[str, Any]], errors)

        error = ApiError(ApiValidationError(payload=payload, debug=repr(exc)))
        return ORJSONResponse(
            status_code=error.status_code,
            content=error.to_json(),
        )
