from types import TracebackType
from typing import Protocol

from domain.project.repository import IProjectRepository


class IUnitOfWork(Protocol):
    project: IProjectRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    async def __aenter__(self) -> "IUnitOfWork": ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType,
    ) -> None: ...
