from collections.abc import AsyncGenerator

import asyncpg
from dishka import Provider, Scope, provide

from application.common.uow import IUnitOfWork
from infrastructure.config.settings import Settings
from infrastructure.database.postgres.init import init_postgres_connection
from infrastructure.database.postgres.uow import PostgresUnitOfWork


class DbProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_db_pool(self, settings: Settings) -> AsyncGenerator[asyncpg.Pool]:
        pool = await asyncpg.create_pool(
            dsn=settings.db_dsn,
            min_size=1,
            max_size=10,
            init=init_postgres_connection,
        )
        try:
            yield pool
        finally:
            await pool.close()

    @provide(scope=Scope.REQUEST)
    async def get_connection(self, pool: asyncpg.Pool) -> AsyncGenerator[asyncpg.Connection]:
        async with pool.acquire() as conn:
            yield conn

    @provide(scope=Scope.REQUEST)
    async def get_uow(self, connection: asyncpg.Connection) -> IUnitOfWork:
        return PostgresUnitOfWork(connection)
