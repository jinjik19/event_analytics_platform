from unittest.mock import MagicMock, patch

import pytest

from infrastructure.security.token_validators.secret_token_validator import SecretTokenValidator


@pytest.fixture
def validator(mock_settings: MagicMock) -> SecretTokenValidator:
    return SecretTokenValidator(settings=mock_settings)


def test_valid_token(validator: SecretTokenValidator) -> None:
    assert validator.validate("test-secret-token-12345") is True

def test_invalid_token(validator: SecretTokenValidator) -> None:
    assert validator.validate("wrong-token") is False

def test_empty_token(validator: SecretTokenValidator) -> None:
    assert validator.validate("") is False

def test_partial_token(validator: SecretTokenValidator) -> None:
    assert validator.validate("test-secret") is False

def test_token_with_extra_chars(validator: SecretTokenValidator) -> None:
    assert validator.validate("test-secret-token-12345-extra") is False

def test_token_different_case(validator: SecretTokenValidator) -> None:
    assert validator.validate("Test-Secret-Token-12345") is False

def test_token_leading_whitespace(validator: SecretTokenValidator) -> None:
    assert validator.validate(" test-secret-token-12345") is False

def test_token_trailing_whitespace(validator: SecretTokenValidator) -> None:
    assert validator.validate("test-secret-token-12345 ") is False

def test_uses_timing_safe_comparison(mock_settings: MagicMock) -> None:
    import secrets

    validator = SecretTokenValidator(settings=mock_settings)

    with patch.object(secrets, "compare_digest", return_value=True) as mock_compare:
        result = validator.validate("any-token")
        mock_compare.assert_called_once_with("test-secret-token-12345", "any-token")
        assert result is True
