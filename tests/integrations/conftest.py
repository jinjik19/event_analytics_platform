import subprocess
from typing import AsyncGenerator, AsyncIterable, Generator
from unittest.mock import patch

import asyncpg
from dishka import Provider, Scope, provide
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from testcontainers.postgres import PostgresContainer
from fakeredis import aioredis

from domain.cache.repository import Cache
from entrypoint.api.main import create_app
from infrastructure.cache.redis import RedisCache
from infrastructure.config.settings import Settings
from infrastructure.database.postgres.init import init_postgres_connection
from infrastructure.database.postgres.repositories.event import PostgresEventRepository
from infrastructure.database.postgres.repositories.project import PostgresProjectRepository
from infrastructure.di.providers.types import CacheRedis


ATLAS_REVISION_TABLE = "atlas_schema_revisions"
TEST_DB_NAME = "test_db"
TEST_DB_USER = "test_user"
TEST_DB_PASSWORD = "test_pass"
TEST_SECRET_TOKEN = "test-secret-token-12345"


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    postgres = PostgresContainer(
        "postgres:17-bookworm",
        dbname=TEST_DB_NAME,
        username=TEST_DB_USER,
        password=TEST_DB_PASSWORD,
    )
    postgres.start()

    yield postgres

    postgres.stop()


@pytest.fixture(scope="session")
def db_settings(postgres_container: PostgresContainer) -> Settings:
    db_host = postgres_container.get_container_host_ip()
    db_port = postgres_container.get_exposed_port(5432)

    return Settings(
        app_env="test",
        db_host=db_host,
        db_port=db_port,
        db_name=TEST_DB_NAME,
        db_user=TEST_DB_USER,
        db_password=TEST_DB_PASSWORD,
        secret_token=TEST_SECRET_TOKEN,
    )


@pytest.fixture(scope="session")
def apply_migrations(db_settings: Settings):
    dsn = str(db_settings.db_dsn) \
        .replace("postgresql+asyncpg://", "postgres://") \
        .replace("postgresql://", "postgres://")
    command = [
        "atlas", "migrate", "apply",
        "--url", f"{dsn}?sslmode=disable",
        "--dir", "file://db/migrations/postgres",
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        error_message = exc.stderr.decode().strip()
        pytest.fail(f"Failed to apply Atlas migrations:\n{error_message}")


@pytest_asyncio.fixture
async def app(
    apply_migrations,
    db_settings: Settings,
    fake_redis_client,
) -> AsyncGenerator[FastAPI, None]:
    class TestSettingsProvider(Provider):
        @provide(scope=Scope.APP)
        def get_settings(self) -> Settings:
            return db_settings

    class TestCacheProvider(Provider):
        scope = Scope.APP

        @provide
        async def get_client(self) -> AsyncIterable[CacheRedis]:
            yield fake_redis_client

        @provide
        def get_cache(self, client: CacheRedis) -> Cache:
            return RedisCache(client)

    with patch("entrypoint.api.main.SettingsProvider", return_value=TestSettingsProvider()), \
        patch("entrypoint.api.main.CacheProvider", return_value=TestCacheProvider()):
        _app = create_app()
        yield _app


@pytest_asyncio.fixture(scope="function")
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TEST_SECRET_TOKEN}"}


@pytest_asyncio.fixture(scope="function")
async def db_conn(db_settings: Settings) -> AsyncGenerator[asyncpg.Connection, None]:
    conn = await asyncpg.connect(db_settings.db_dsn)
    await init_postgres_connection(conn)

    yield conn
    await conn.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clean_tables(db_conn: asyncpg.Connection):
    rows = await db_conn.fetch("""
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    """)

    tables_to_truncate = [
        f'"{r["tablename"]}"' for r in rows
        if r["tablename"] != ATLAS_REVISION_TABLE
    ]

    if not tables_to_truncate:
        return

    await db_conn.execute(
        f"TRUNCATE TABLE {', '.join(tables_to_truncate)} RESTART IDENTITY CASCADE;"
    )


@pytest_asyncio.fixture
async def project_repository(db_conn):
    return PostgresProjectRepository(connection=db_conn)


@pytest_asyncio.fixture
async def event_repository(db_conn):
    return PostgresEventRepository(connection=db_conn)


@pytest.fixture
async def fake_redis_client():
    client = aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.close()


@pytest.fixture
def fake_redis_cache(fake_redis_client):
    return RedisCache(redis=fake_redis_client)
