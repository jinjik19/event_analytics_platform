from domain.event.repository import (
    EventCountByDay,
    EventFunnelParams,
    EventFunnelResul,
    EventTopProductsParams,
    EventTopProductsResul,
)
from domain.event.types import AnalyticsMetrics, EventType
from domain.types import ProjectID
from infrastructure.database.clickhouse.base import ClickhouseBaseRepository


class EventAnalyticsRepository(ClickhouseBaseRepository):
    async def count_event_by_day(self, project_id: ProjectID) -> list[EventCountByDay]:
        result = await self.query(
            """
            SELECT
                toDate(timestamp) AS event_date,
                COUNT(event_id) AS total
            FROM raw.event
            WHERE project_id = {project_id:UUID}
            GROUP BY event_date
            ORDER BY event_date
            """,
            parameters={"project_id": project_id},
        )

        return [EventCountByDay(date=row[0], count=row[1]) for row in result.result_rows]

    async def funnel(self, params: EventFunnelParams) -> list[EventFunnelResul]:
        step_conditions = ",\n".join(f"event_type = '{step.value}'" for step in params.steps)
        case_when = "\n".join(
            f"WHEN {i + 1} THEN '{step.value}'" for i, step in enumerate(params.steps)
        )
        step_array = "[" + ", ".join(str(i + 1) for i in range(len(params.steps))) + "]"

        query = f"""
            WITH funnel AS (
                SELECT
                    user_id,
                    windowFunnel({{window_days:UInt64}})(
                        toUnixTimestamp("timestamp"),
                        {step_conditions}
                    ) AS level
                FROM raw.event
                WHERE project_id = {{project_id:UUID}}
                    AND toDate(timestamp) >= {{date_from:Date32}}
                    AND toDate(timestamp) <= {{date_to:Date32}}
                GROUP BY user_id
            ), steps AS (
                SELECT
                    s AS step,
                    CASE s
                        {case_when}
                    END AS event_name,
                    countIf(level >= s) AS users
                FROM funnel
                ARRAY JOIN {step_array} AS s
                WHERE level > 0
                GROUP BY step, event_name
            )
            SELECT
                step,
                event_name,
                users,
                ROUND(
                    users * 100.0 / nullIf(LAG(users) OVER (ORDER BY step), 0), 1
                ) AS conversion_from_prev,
                ROUND(
                    users * 100.0 / nullIf(FIRST_VALUE(users) OVER (ORDER BY step), 0), 1
                ) AS conversion_from_top
            FROM steps
            ORDER BY step
        """  # noqa: S608

        result = await self.query(
            query,
            parameters={
                "project_id": params.project_id,
                "date_from": params.date_from,
                "date_to": params.date_to,
                "window_days": params.window_days * 24 * 60 * 60,
            },
        )

        return [
            EventFunnelResul(
                step=EventType(row[1]),  # row[1] = event_name → EventType
                users=row[2],  # row[2] = users
                conversion_from_prev=row[3],  # row[3] = conversion_from_prev
                conversion_from_top=row[4],  # row[4] = conversion_from_top
            )
            for row in result.result_rows
        ]

    async def top_products(self, params: EventTopProductsParams) -> list[EventTopProductsResul]:
        METRICS_ORDER_MAP = {  # noqa: N806
            AnalyticsMetrics.BY_CART: "add_to_cart_count DESC",
            AnalyticsMetrics.BY_REVENUE: "revenue DESC, purchase_count DESC",
        }
        order_col = METRICS_ORDER_MAP[params.metric]

        query = f"""
            SELECT
                category,
                product_id,
                argMax(product_name, timestamp) AS product_name,
                countIf(event_type = 'add_to_cart') AS add_to_cart_count,
                countIf(event_type = 'purchase') AS purchase_count,
                sumIf(
                    JSONExtractFloat(properties, 'price') * JSONExtractUInt(properties, 'quantity'),
                    event_type = 'purchase'
                ) AS revenue
            FROM raw."event"
            WHERE project_id = {{project_id:UUID}}
                AND product_id != ''
                AND event_type IN ('add_to_cart', 'purchase')
                AND toDate(timestamp) >= {{date_from:Date32}}
                AND toDate(timestamp) <= {{date_to:Date32}}
            GROUP BY category, product_id
            ORDER BY {order_col}
            LIMIT {{limit:UInt32}}
        """  # noqa: S608

        result = await self.query(
            query,
            parameters={
                "project_id": params.project_id,
                "date_from": params.date_from,
                "date_to": params.date_to,
                "limit": params.limit,
            },
        )

        return [
            EventTopProductsResul(
                category=row[0],
                product_id=row[1],
                product_name=row[2],
                add_to_cart_count=row[3],
                purchase_count=row[4],
                revenue=row[5],
            )
            for row in result.result_rows
        ]
