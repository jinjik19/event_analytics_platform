from typing import Protocol


class TokenValidator(Protocol):
    def validate(self, incoming_token: str) -> bool: ...
