# 2. Use structlog for logging

Date: 2026-01-07
Status: Accepted

## Context

The platform requires a robust logging solution to monitor application behavior and troubleshoot issues.

I have distinct requirements for different environments:

- **Development:** Logs should be human-readable (colored text) in the console for easy debugging.
- **Production:** Logs must be machine-readable (JSON) for ingestion into the observability stack (Prometheus/Loki/Grafana).

The standard Python `logging` module is primarily designed for text processing. While it can produce JSON, doing so requires complex configuration and often lacks flexibility in handling context variables in asynchronous environments (FastAPI).

## Decision

I will use **structlog** as the primary logging library for the platform.

It will be configured to wrap the standard library's logger, ensuring compatibility with third-party libraries, while providing a modern API for our application code.

## Consequences

### Positive

- **Structured Data First:** Encourages logging events as data (key-value pairs) rather than formatted strings, which significantly improves query capabilities in Loki.
- **Environment Adaptability:** Easy to switch between `ConsoleRenderer` (Dev) and `JSONRenderer` (Prod) using processor chains.
- **Async & Context Support:** Native support for `contextvars`, making it easy to bind trace IDs or request IDs across async tasks in FastAPI.
- **Performance:** Lightweight core with lower overhead compared to standard logging when configured correctly.

### Negative

- **Learning Curve:** I need to learn the new API (e.g., using `log.bind()` instead of formatting strings).
- **Configuration Complexity:** Initial setup requires understanding processor chains to correctly handle standard library interoperability.
