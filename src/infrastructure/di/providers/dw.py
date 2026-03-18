from collections.abc import AsyncGenerator

import clickhouse_connect
from clickhouse_connect.driver.asyncclient import AsyncClient
from dishka import Provider, Scope, provide

from domain.event.repository import IEventAnalyticsRepository
from infrastructure.config.settings import Settings
from infrastructure.database.clickhouse.repositories.event import EventAnalyticsRepository


class DWProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_clickhouse_client(self, settings: Settings) -> AsyncGenerator[AsyncClient]:
        client = await clickhouse_connect.get_async_client(
            host=settings.dwh_host,
            port=settings.dwh_port,
            username=settings.dwh_user,
            password=settings.dwh_password,
            database=settings.dwh_database,
        )
        try:
            yield client
        finally:
            await client.close()

    @provide(scope=Scope.REQUEST)
    async def get_event_analytics_repo(self, client: AsyncClient) -> IEventAnalyticsRepository:
        return EventAnalyticsRepository(client)
