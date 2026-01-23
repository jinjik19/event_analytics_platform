from dishka import Provider, Scope, provide

from infrastructure.config.settings import Settings
from infrastructure.security.token_validators.secret_token_validator import SecretTokenValidator


class SecurityProvider(Provider):
    scope = Scope.APP

    @provide
    def get_secret_token_validator(self, settings: Settings) -> SecretTokenValidator:
        return SecretTokenValidator(settings=settings)
