from typing import Any, Protocol


class Cache(Protocol):
    async def set(self, key: str, value: Any, ttl: int) -> None: ...  # noqa: ANN401

    async def get(self, key: str) -> Any | None: ...  # noqa: ANN401
