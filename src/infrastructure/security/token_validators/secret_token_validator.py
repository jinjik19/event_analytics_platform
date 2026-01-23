import secrets

from infrastructure.config.settings import Settings


class SecretTokenValidator:
    def __init__(self, settings: Settings) -> None:
        self._expected_token = settings.secret_token

    def validate(self, incoming_token: str) -> bool:
        return secrets.compare_digest(self._expected_token, incoming_token)
