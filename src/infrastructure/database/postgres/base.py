from typing import cast

import asyncpg


class PostgresBaseRepository:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self._connection = connection

    async def execute(self, query: str, *args: object) -> None:
        """Wrapper for (INSERT, UPDATE, DELETE)

        Attrs:
            query: SQL query in string format
        """
        await self._connection.execute(query, *args)

    async def fetch_one(self, query: str, *args: object) -> asyncpg.Record | None:
        """Wrapper for get one row

        Attrs:
            query: SQL query in string format
        """
        return await self._connection.fetchrow(query, *args)

    async def fetch_all(self, query: str, *args: object) -> list[asyncpg.Record]:
        """Wrapper for get rows

        Attrs:
            query: SQL query in string format
        """
        result = await self._connection.fetch(query, *args)
        return cast(list[asyncpg.Record], result)
