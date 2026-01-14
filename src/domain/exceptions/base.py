from collections.abc import Mapping
from typing import Any

from domain.utils.formatting import split_camel_case
from infrastructure.config.settings import settings


class BaseError(Exception):
    def __init__(
        self,
        message: str | None = None,
        payload: Mapping[str, Any] | list[dict[str, Any]] | None = None,
        debug: Any | None = None,  # noqa: ANN401
    ) -> None:
        self.message = message or " ".join(split_camel_case(type(self).__name__)).title()
        self.payload = payload
        self.debug = debug

    @classmethod
    def code(cls) -> str:
        return cls.__name__

    def to_json(self) -> Mapping[str, Any]:
        return {
            "code": self.code(),
            "message": self.message,
            "payload": self.payload,
            "debug": self.debug if settings.debug else None,
        }
