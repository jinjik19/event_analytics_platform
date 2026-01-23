from collections.abc import Callable, Coroutine
from typing import Any

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Request, Response

from infrastructure.rate_limit.types import RateLimiterProto


def rate_limit_dependency[T: RateLimiterProto](
    limiter_cls: type[T],
) -> Callable[[Request, Response, T], Coroutine[Any, Any, None]]:
    @inject
    async def rate_limit_check(
        request: Request,
        response: Response,
        limiter: FromDishka[limiter_cls],  # type: ignore
    ) -> None:
        await limiter(request, response)  # type: ignore[misc]

    return rate_limit_check
