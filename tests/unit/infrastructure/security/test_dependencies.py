from unittest.mock import MagicMock

import pytest

from domain.exceptions.app import ForbiddenError
from infrastructure.security.dependencies import token_auth_required

_token_auth = token_auth_required.__dishka_orig_func__


def _make_request(authorization: str | None) -> MagicMock:
    request = MagicMock()
    request.headers = MagicMock()
    request.headers.get = MagicMock(return_value=authorization)
    return request


async def test_valid_bearer_token(mock_validator: MagicMock) -> None:
    request = _make_request("Bearer valid-token")

    await _token_auth(request=request, validator=mock_validator)

    mock_validator.validate.assert_called_once_with("valid-token")

async def test_invalid_token_raises_forbidden(mock_validator: MagicMock) -> None:
    mock_validator.validate.return_value = False
    request = _make_request("Bearer wrong-token")

    with pytest.raises(ForbiddenError) as exc_info:
        await _token_auth(request=request, validator=mock_validator)

    assert exc_info.value.message == "Invalid secret token"
    mock_validator.validate.assert_called_once_with("wrong-token")

async def test_missing_header_raises_forbidden(mock_validator: MagicMock) -> None:
    request = _make_request(None)

    with pytest.raises(ForbiddenError) as exc_info:
        await _token_auth(request=request, validator=mock_validator)

    assert exc_info.value.message == "Missing Authorization header"
    mock_validator.validate.assert_not_called()

async def test_missing_bearer_prefix_raises_forbidden(mock_validator: MagicMock) -> None:
    request = _make_request("Token some-token")

    with pytest.raises(ForbiddenError) as exc_info:
        await _token_auth(request=request, validator=mock_validator)

    assert exc_info.value.message == "Invalid authorization header format"
    mock_validator.validate.assert_not_called()

async def test_empty_authorization_raises_forbidden(mock_validator: MagicMock) -> None:
    request = _make_request("")

    with pytest.raises(ForbiddenError) as exc_info:
        await _token_auth(request=request, validator=mock_validator)

    assert exc_info.value.message == "Invalid authorization header format"
    mock_validator.validate.assert_not_called()

async def test_bearer_without_space_raises_forbidden(mock_validator: MagicMock) -> None:
    request = _make_request("Bearertoken")

    with pytest.raises(ForbiddenError) as exc_info:
        await _token_auth(request=request, validator=mock_validator)

    assert exc_info.value.message == "Invalid authorization header format"
    mock_validator.validate.assert_not_called()

async def test_lowercase_bearer_raises_forbidden(mock_validator: MagicMock) -> None:
    request = _make_request("bearer valid-token")

    with pytest.raises(ForbiddenError) as exc_info:
        await _token_auth(request=request, validator=mock_validator)

    assert exc_info.value.message == "Invalid authorization header format"
    mock_validator.validate.assert_not_called()

async def test_basic_auth_raises_forbidden(mock_validator: MagicMock) -> None:
    request = _make_request("Basic dXNlcjpwYXNz")

    with pytest.raises(ForbiddenError) as exc_info:
        await _token_auth(request=request, validator=mock_validator)

    assert exc_info.value.message == "Invalid authorization header format"
    mock_validator.validate.assert_not_called()

async def test_bearer_with_empty_token(mock_validator: MagicMock) -> None:
    mock_validator.validate.return_value = False
    request = _make_request("Bearer ")

    with pytest.raises(ForbiddenError) as exc_info:
        await _token_auth(request=request, validator=mock_validator)

    assert exc_info.value.message == "Invalid secret token"
    mock_validator.validate.assert_called_once_with("")

async def test_bearer_with_spaces_in_token(mock_validator: MagicMock) -> None:
    request = _make_request("Bearer token with spaces")

    await _token_auth(request=request, validator=mock_validator)

    mock_validator.validate.assert_called_once_with("token with spaces")

async def test_only_bearer_prefix_stripped(mock_validator: MagicMock) -> None:
    request = _make_request("Bearer Bearer nested")

    await _token_auth(request=request, validator=mock_validator)

    mock_validator.validate.assert_called_once_with("Bearer nested")

async def test_header_key_is_authorization(mock_validator: MagicMock) -> None:
    request = _make_request("Bearer token")

    await _token_auth(request=request, validator=mock_validator)

    request.headers.get.assert_called_once_with("Authorization")
