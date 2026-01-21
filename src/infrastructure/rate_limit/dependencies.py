from fastapi import Request, Response
from fastapi_limiter.depends import RateLimiter

from application.common.uow import IUnitOfWork
from domain.cache.repository import Cache
from domain.exceptions.app import RateLimitExceededError
from infrastructure.config.settings import Settings
from infrastructure.rate_limit.config import get_plan_rate_limit


class PlanBasedRateLimiter:
    """Rate limiter for event endpoints based on project plan.

    If a valid API key is provided, applies plan-based rate limiting.
    If no API key or invalid key, falls back to IP-based rate limiting.
    """

    def __init__(self, settings: Settings, uow: IUnitOfWork, cache: Cache) -> None:
        self._settings = settings
        self._uow = uow
        self._cache = cache

    async def __call__(self, request: Request, response: Response) -> None:
        if not self._settings.is_rate_limit_enabled:
            return

        api_key = request.headers.get("X-Api-Key")
        identifier_str, rpm = await self._get_identifier_and_rpm(api_key, request)

        async def get_identifier(request: Request) -> str:
            return identifier_str

        limiter = RateLimiter(
            times=rpm,
            seconds=60,
            identifier=get_identifier,
        )

        try:
            await limiter(request, response)
        except Exception as exc:
            if hasattr(exc, "detail") and "Too Many Requests" in str(exc.detail):
                raise RateLimitExceededError(retry_after=60) from exc
            raise

    async def _get_identifier_and_rpm(
        self, api_key: str | None, request: Request
    ) -> tuple[str, int]:
        """Get rate limit identifier and requests per minute."""
        if not api_key or not api_key.startswith(f"wk_{self._settings.app_env}"):
            return self._get_ip_identifier(request), self._settings.rate_limit_no_auth_rpm

        # Try to get project from cache
        cache_api_key = f"api_key:{api_key}"
        if cached_project_id := await self._cache.get(cache_api_key):
            project = await self._uow.project.get_by_id(cached_project_id)
            if project:
                rpm = get_plan_rate_limit(project.plan, self._settings)
                return f"project:{project.project_id}", rpm

        # Try to get project from database
        project = await self._uow.project.get_by_api_key(api_key)
        if project:
            await self._cache.set(api_key, project.project_id)
            rpm = get_plan_rate_limit(project.plan, self._settings)
            return f"project:{project.project_id}", rpm

        # Invalid API key - fallback to IP-based limit
        return self._get_ip_identifier(request), self._settings.rate_limit_no_auth_rpm

    def _get_ip_identifier(self, request: Request) -> str:
        """Get IP-based identifier for rate limiting."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
            return f"ip:{ip}"

        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"


class IPRateLimiter:
    """IP-based rate limiter for project creation and anonymous requests."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def __call__(self, request: Request, response: Response) -> None:
        if not self._settings.is_rate_limit_enabled:
            return

        # Future: Check X-Secret-Token header for admin operations
        # secret_token = request.headers.get("X-Secret-Token")
        # if secret_token and validate_secret_token(secret_token):
        #     return  # No rate limit for valid secret token

        client_ip = request.client.host if request.client else "unknown"
        identifier_str = f"project_create:{client_ip}"

        async def get_identifier(request: Request) -> str:
            return identifier_str

        limiter = RateLimiter(
            times=self._settings.rate_limit_project_create_rpm,
            seconds=60,
            identifier=get_identifier,
        )

        try:
            await limiter(request, response)
        except Exception as exc:
            if hasattr(exc, "detail") and "Too Many Requests" in str(exc.detail):
                raise RateLimitExceededError(retry_after=60) from exc
            raise
