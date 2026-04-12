from domain.event.repository import (
    EventCountByDay,
    EventFunnelParams,
    EventFunnelResult,
    EventRetentionParams,
    EventRetentionResult,
    EventTopCountriesParams,
    EventTopCountriesResult,
    EventTopProductsParams,
    EventTopProductsResult,
)
from domain.event.types import AnalyticsMetrics, CountriesMetrics, EventType
from domain.types import ProjectID
from infrastructure.database.clickhouse.base import ClickhouseBaseRepository


class EventAnalyticsRepository(ClickhouseBaseRepository):
    async def count_event_by_day(self, project_id: ProjectID) -> list[EventCountByDay]:
        result = await self.query(
            """
            SELECT
                event_date,
                events AS total
            FROM analytics.mart_events_per_day
            WHERE project_id = {project_id:UUID}
            ORDER BY event_date
            """,
            parameters={"project_id": project_id},
        )

        return [EventCountByDay(date=row[0], count=row[1]) for row in result.result_rows]

    async def funnel(self, params: EventFunnelParams) -> list[EventFunnelResult]:
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
                FROM analytics.stg_events
                WHERE project_id = {{project_id:UUID}}
                    AND event_date >= {{date_from:Date32}}
                    AND event_date <= {{date_to:Date32}}
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
            EventFunnelResult(
                step=EventType(row[1]),  # row[1] = event_name → EventType
                users=row[2],  # row[2] = users
                conversion_from_prev=row[3],  # row[3] = conversion_from_prev
                conversion_from_top=row[4],  # row[4] = conversion_from_top
            )
            for row in result.result_rows
        ]

    async def top_products(self, params: EventTopProductsParams) -> list[EventTopProductsResult]:
        METRICS_ORDER_MAP = {  # noqa: N806
            AnalyticsMetrics.BY_CART: "add_to_cart_count DESC",
            AnalyticsMetrics.BY_REVENUE: "revenue DESC, purchase_count DESC",
        }
        order_col = METRICS_ORDER_MAP[params.metric]

        query = f"""
            SELECT
                category,
                product_id,
                argMax(product_name, event_date) AS product_name,
                SUM(add_to_cart_count) AS add_to_cart_count,
                SUM(purchase_count) AS purchase_count,
                SUM(revenue) AS revenue
            FROM analytics.mart_top_products
            WHERE project_id = {{project_id:UUID}}
                AND event_date >= {{date_from:Date32}}
                AND event_date <= {{date_to:Date32}}
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
            EventTopProductsResult(
                category=row[0],
                product_id=row[1],
                product_name=row[2],
                add_to_cart_count=row[3],
                purchase_count=row[4],
                revenue=row[5],
            )
            for row in result.result_rows
        ]

    async def retention(self, params: EventRetentionParams) -> list[EventRetentionResult]:
        query = """
            SELECT
                cohort_date,
                day_number,
                retained_users,
                cohort_size,
                retention_pct
            FROM analytics.mart_retention
            WHERE project_id = {project_id:UUID}
                AND cohort_date >= {date_from:Date32}
                AND cohort_date <= {date_to:Date32}
                AND day_number <= {days:UInt16}
            ORDER BY cohort_date, day_number
        """

        result = await self.query(
            query,
            parameters={
                "project_id": params.project_id,
                "date_from": params.date_from,
                "date_to": params.date_to,
                "days": params.days,
            },
        )

        return [
            EventRetentionResult(
                cohort_date=row[0],
                day_number=row[1],
                retained_users=row[2],
                cohort_size=row[3],
                retention_pct=row[4],
            )
            for row in result.result_rows
        ]

    async def top_countries(self, params: EventTopCountriesParams) -> list[EventTopCountriesResult]:
        SORT_ORDER_MAP = {  # noqa: N806
            CountriesMetrics.BY_USERS: "unique_users DESC",
            CountriesMetrics.BY_EVENTS: "event_count DESC",
            CountriesMetrics.BY_REVENUE: "revenue DESC",
        }
        sort_col = SORT_ORDER_MAP[params.sort_by]

        query = f"""
            SELECT
                country,
                uniqMerge(unique_users_state) AS unique_users,
                countMerge(event_count) AS event_count,
                sumIfMerge(revenue) AS revenue
            FROM analytics.mart_top_countries
            WHERE project_id = {{project_id:UUID}}
                AND event_date >= {{date_from:Date32}}
                AND event_date <= {{date_to:Date32}}
            GROUP BY country
            ORDER BY {sort_col}
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
            EventTopCountriesResult(
                country=row[0],
                unique_users=row[1],
                events_count=row[2],
                revenue=row[3],
            )
            for row in result.result_rows
        ]
