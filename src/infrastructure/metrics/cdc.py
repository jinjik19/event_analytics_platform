import asyncio

import httpx
from prometheus_client import Gauge
from structlog import BoundLogger

from infrastructure.config.settings import Settings
from infrastructure.database.clickhouse.base import ClickhouseBaseRepository


CDC_E2E_LAG = Gauge(
    "cdc_e2e_lag",
    "E2E lag between PostgreSQL and ClickHouse",
)


class CdcLagMonitor:
    def __init__(
        self,
        dwh_repo: ClickhouseBaseRepository,
        http_client: httpx.AsyncClient,
        logger: BoundLogger,
        settings: Settings,
    ) -> None:
        self._dwh_repo = dwh_repo
        self._http_client = http_client
        self._logger = logger
        self._settings = settings

    async def run(self) -> None:
        while True:
            try:
                await self._check_debezium()
                await self._check_e2e_lag()
            except asyncio.CancelledError as e:
                self._logger.info("cdc_task_cancelled", error=str(e))
                break
            except Exception as e:
                self._logger.error("cdc_unexpected_error", error=str(e))

            await asyncio.sleep(self._settings.cdc_lag_interval)

    async def _check_debezium(self) -> None:
        try:
            url = f"{self._settings.debezium_url}/connectors"
            result = await self._http_client.get(url)
            result.raise_for_status()
            connectors = result.json()

            for connector in connectors:
                result = await self._http_client.get(f"{url}/{connector}/status")
                result.raise_for_status()
                data = result.json()
                state = data["connector"]["state"]
                self._logger.info("debezium_metrics", name=connector, state=state)
        except Exception as e:
            self._logger.error("debezium_check_failed", error=str(e))
            raise

    async def _check_e2e_lag(self) -> None:
        try:
            result = await self._dwh_repo.query("SELECT now() - max(created_at) FROM raw.event")
            CDC_E2E_LAG.set(result.result_rows[0][0])
        except Exception as e:
            self._logger.error("e2e_lag_check_failed", error=str(e))
            raise
