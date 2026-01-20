from domain.project.types import Plan
from infrastructure.config.settings import Settings


def get_plan_rate_limit(plan: Plan, settings: Settings) -> int:
    """Return requests per minute based on plan."""
    return {
        Plan.FREE: settings.rate_limit_free_rpm,
        Plan.PRO: settings.rate_limit_pro_rpm,
        Plan.ENTERPRISE: settings.rate_limit_enterprise_rpm,
    }.get(plan, settings.rate_limit_no_auth_rpm)
