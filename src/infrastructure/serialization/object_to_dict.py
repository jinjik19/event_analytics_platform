from typing import Any


class ObjectDictSerializer:
    @staticmethod
    def to_dict(obj: object) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for attr in dir(obj):
            if attr.startswith("_"):
                continue

            value = getattr(obj, attr, None)

            if callable(value):
                continue

            result[attr] = value

        return result
