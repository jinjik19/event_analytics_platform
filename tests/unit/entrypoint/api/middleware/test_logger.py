import pytest
import structlog
from unittest.mock import AsyncMock, MagicMock, patch
from starlette.types import Scope, Receive, Send

from entrypoint.api.middleware.logger import StructlogMiddleware


# --- FIXTURES ---

@pytest.fixture(name="mock_app")
def fixture_mock_app():
    return AsyncMock()

@pytest.fixture(name="middleware")
def fixture_middleware(mock_app):
    return StructlogMiddleware(app=mock_app)

@pytest.fixture(name="scope")
def fixture_scope():
    return {
        "type": "http",
        "path": "/api/v1/test",
        "method": "GET",
        "headers": [
            (b"user-agent", b"pytest-agent"),
            (b"x-request-id", b"123-custom-id"),
            (b"x-forwarded-for", b"10.0.0.1"),
        ],
        "client": ("127.0.0.1", 8000),
    }

@pytest.fixture(name="receive")
def fixture_receive():
    return AsyncMock()

@pytest.fixture(name="send")
def fixture_send():
    return AsyncMock()


# --- TESTS ---

@pytest.mark.asyncio
async def test_call_non_http_scope(middleware, mock_app, receive, send):
    scope = {"type": "lifespan"}

    await middleware(scope, receive, send)

    mock_app.assert_awaited_once_with(scope, receive, send)
    with patch("structlog.contextvars.bind_contextvars") as mock_bind:
        await middleware(scope, receive, send)
        mock_bind.assert_not_called()

@pytest.mark.asyncio
async def test_call_ignored_path(middleware, mock_app, scope, receive, send):
    scope["path"] = "/healthz"

    with structlog.testing.capture_logs() as cap_logs:
        await middleware(scope, receive, send)

    mock_app.assert_awaited_once()
    assert len(cap_logs) == 0

@pytest.mark.asyncio
async def test_successful_request_logging(middleware, mock_app, scope, receive, send):
    async def app_side_effect(sc, rec, snd):
        await snd({"type": "http.response.start", "status": 201})

    mock_app.side_effect = app_side_effect

    with patch("structlog.contextvars.bind_contextvars") as mock_bind:
        with structlog.testing.capture_logs() as cap_logs:
            await middleware(scope, receive, send)

        mock_bind.assert_called()
        call_kwargs = mock_bind.call_args[1]
        assert call_kwargs["request_id"] == "123-custom-id"
        assert call_kwargs["user_agent"] == "pytest-agent"
        assert call_kwargs["client_ip"] == "127.0.0.1"
        assert call_kwargs["method"] == "GET"

    assert len(cap_logs) == 1
    log = cap_logs[0]
    assert log["event"] == "request_completed"
    assert log["status_code"] == 201
    assert "duration" in log
    assert log["log_level"] == "info"

@pytest.mark.asyncio
async def test_generate_request_id_if_missing(middleware, mock_app, scope, receive, send):
    """Если заголовка x-request-id нет, middleware должен сгенерировать UUID."""
    scope["headers"] = []

    with patch("structlog.contextvars.bind_contextvars") as mock_bind:
        await middleware(scope, receive, send)

        call_kwargs = mock_bind.call_args[1]
        request_id = call_kwargs["request_id"]
        assert request_id is not None
        assert len(request_id) > 10

@pytest.mark.asyncio
async def test_exception_logging(middleware, mock_app, scope, receive, send):
    mock_app.side_effect = ValueError("Database error")

    with structlog.testing.capture_logs() as cap_logs:
        with pytest.raises(ValueError, match="Database error"):
            await middleware(scope, receive, send)

    assert len(cap_logs) == 1
    log = cap_logs[0]
    assert log["event"] == "request_failed"
    assert log["status_code"] == 500
    assert log["error"] == "Database error"
    assert log["log_level"] == "error"

@pytest.mark.asyncio
async def test_client_ip_fallback(middleware, mock_app, scope, receive, send):
    scope["client"] = None

    with patch("structlog.contextvars.bind_contextvars") as mock_bind:
        await middleware(scope, receive, send)

        call_kwargs = mock_bind.call_args[1]
        assert call_kwargs["client_ip"] == "unknown"
