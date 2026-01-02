# 1. Use FastAPI for Backend Service

Date: 2026-01-02
Status: Accepted

## Context

I am building an Event Analytics Platform (Stage 1) that needs to handle a high throughput of events.
The key requirements are:

- **Performance:** The system must process approximately 1,000 requests per second.
- **Workload:** The main operations are I/O-bound (writing data to Redis and PostgreSQL).
- **Maintainability:** I need strong data validation and up-to-date documentation for the API.

I considered using synchronous frameworks (like Django or Flask) versus asynchronous frameworks. Synchronous frameworks use a thread-per-request model, where each thread consumes significant memory (~2MB stack size). Scaling this to thousands of concurrent connections leads to high memory overhead and context-switching costs.

## Decision

I will use **FastAPI** as the main web framework for the backend service.

## Consequences

### Positive

- **Resource Efficiency:** FastAPI is async-native (built on Starlette). It uses an event loop and coroutines, allowing it to handle thousands of concurrent connections with minimal memory footprint compared to thread-based blocking I/O.
- **Data Integrity:** Deep integration with **Pydantic** allows us to use Python type hints for automatic request validation. This reduces boilerplate code for checking JSON payloads.
- **Developer Experience:** It automatically generates interactive API documentation (Swagger UI / OpenAPI), which simplifies testing and integration for client developers.

### Negative

- **Complexity:** Asynchronous code can be harder to debug than synchronous code. I must ensure that I do not use blocking calls (e.g., standard `time.sleep` or blocking DB drivers) inside async route handlers.
