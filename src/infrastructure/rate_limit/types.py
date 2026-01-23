from typing import Protocol

from fastapi import Request, Response


class RateLimiterProto(Protocol):
    async def __call__(self, request: Request, response: Response) -> None: ...
