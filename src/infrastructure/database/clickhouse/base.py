from clickhouse_connect.driver.asyncclient import AsyncClient
from clickhouse_connect.driver.query import QueryResult


class ClickhouseBaseRepository:
    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def query(
        self,
        query: str,
        parameters: dict | None = None,
    ) -> QueryResult:
        return await self._client.query(query, parameters=parameters)

    async def insert(
        self,
        table: str,
        data: list[list],
        column_names: list[str],
    ) -> None:
        await self._client.insert(table, data, column_names=column_names)

    async def command(self, cmd: str) -> None:
        await self._client.command(cmd)
