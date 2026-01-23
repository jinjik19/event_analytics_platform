from dishka import Provider, Scope, provide

from application.common.uow import IUnitOfWork
from domain.cache.repository import Cache
from infrastructure.config.settings import Settings
from infrastructure.rate_limit.dependencies import IPRateLimiter, PlanBasedRateLimiter
from infrastructure.security.token_validators.secret_token_validator import SecretTokenValidator


class RateLimitProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_plan_based_limiter(
        self,
        settings: Settings,
        uow: IUnitOfWork,
        cache: Cache,
    ) -> PlanBasedRateLimiter:
        return PlanBasedRateLimiter(settings=settings, uow=uow, cache=cache)

    @provide
    def get_ip_limiter(
        self, settings: Settings, token_validator: SecretTokenValidator
    ) -> IPRateLimiter:
        return IPRateLimiter(settings=settings, token_validator=token_validator)
