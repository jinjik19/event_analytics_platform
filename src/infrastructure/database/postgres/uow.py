from types import TracebackType

import asyncpg
from asyncpg.transaction import Transaction

from infrastructure.database.postgres.repositories.project import PostgresProjectRepository


class PostgresUnitOfWork:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self._connection: asyncpg.Connection = connection
        self._transaction: Transaction = None

        self.project = PostgresProjectRepository(connection)

    async def __aenter__(self) -> "PostgresUnitOfWork":
        self._transaction = self._connection.transaction()
        await self._transaction.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType,
    ) -> None:
        if exc_value:
            await self._transaction.rollback()

    async def commit(self) -> None:
        if self._transaction:
            await self._transaction.commit()

    async def rollback(self) -> None:
        if self._transaction:
            await self._transaction.rollback()
