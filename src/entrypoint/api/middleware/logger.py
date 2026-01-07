import time
import uuid

import structlog
from starlette.types import ASGIApp, Message, Receive, Scope, Send


logger = structlog.get_logger("api")


class StructlogMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if self._should_ignore(path):
            await self.app(scope, receive, send)
            return

        self._bind_logs(scope)

        await self._process_request(scope, receive, send)

    def _should_ignore(self, path: str) -> bool:
        """Check if the path should be ignored for logging."""
        return path in ("/healthz", "/health", "/ready")

    def _bind_logs(self, scope: Scope) -> None:
        """Extract headers and bind them to structlog context."""
        headers = dict(scope.get("headers", []))

        # Parse Request ID or generate a new Request ID
        request_id = headers.get(b"x-request-id", b"").decode("latin1") or str(uuid.uuid4())
        user_agent = headers.get(b"user-agent", b"").decode("latin1") or "unknown"

        client = scope.get("client")
        client_ip = client[0] if client else "unknown"

        method = scope.get("method", "UNKNOWN")

        # Bind context structlog logger
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=method,
            path=scope.get("path", ""),
            client_ip=client_ip,
            user_agent=user_agent,
        )

    async def _process_request(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process the incoming request."""
        status_code = [500]
        start_time = time.perf_counter()

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)

            process_time = time.perf_counter() - start_time
            logger.info(
                "request_completed",
                status_code=status_code[0],
                duration=process_time,
            )
        except Exception as exc:
            process_time = time.perf_counter() - start_time
            logger.exception(
                "request_failed",
                status_code=500,
                duration=process_time,
                error=str(exc),
            )
            raise exc
