import pytest
from fastapi import status
from domain.exceptions.base import BaseError
from entrypoint.api.exceptions import (
    get_status_code,
    exception_to_response_schema,
    exception_to_example
)


class MyNotFound(BaseError):
    @property
    def message(self):
        return "Not found"


class MyCustomError(BaseError):
    @property
    def message(self):
        return "Error"

def test_get_status_code_mapped():
    class NotFoundError(BaseError):
        pass

    assert get_status_code(NotFoundError()) == status.HTTP_404_NOT_FOUND

def test_exception_to_schema():
    class ValidationError(BaseError):
        pass

    exc = ValidationError()
    schema = exception_to_response_schema(exc)

    assert 422 in schema
    content = schema[422]["content"]["application/json"]
    assert "schema" in content
    assert "examples" in content
    assert content["examples"]["ValidationError"]["value"]["code"] == "ValidationError"

def test_exception_to_example():
    class TestError(BaseError):
        pass

    exc = TestError()
    example = exception_to_example(exc)

    assert "TestError" in example
    assert example["TestError"]["value"]["code"] == "TestError"
