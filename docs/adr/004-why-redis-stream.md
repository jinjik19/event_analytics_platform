# 4. Use Redis Streams for Event Ingestion Buffer

Date: 2026-02-06
Status: Accepted

## Context

I am building an event analytics platform with a target ingestion rate of **1,000 events per second**.
Since the API supports batch ingestion (`/batch`), the actual HTTP request rate (RPS) will be significantly lower than the event rate, depending on the client batch size.

However, the architecture must ensure:

1.  **Low Latency:** The API must accept batches quickly (`202 Accepted`) regardless of the database write speed.
2.  **Reliability:** I must not lose any events from the accepted batches if a background worker crashes.
3.  **Simplicity:** As a solo developer, I need a stack that is easy to maintain.

I evaluated these options:

- **Direct DB Write:** Even with batching, synchronous writes couple the API availability to the database performance.
- **Redis Lists (`RPUSH`/`LPOP`):** Simple, but lacks reliable delivery. If a worker crashes while processing a batch, the whole batch is lost.
- **Apache Kafka:** Overkill for 1,000 events/s. High operational cost.
- **Redis Streams:** Lightweight, reliable, and supports consumer groups.

## Decision

I decided to use **Redis Streams** as the buffer between the API and the background workers.

### Why Redis Streams?

1.  **Reliability (The main reason):** Unlike Redis Lists, Redis Streams use **Acknowledgements (`XACK`)**. If a worker crashes while processing a batch of events, the message remains in the "Pending" state and can be re-processed by another worker. This guarantees "at-least-once" delivery for every batch.
2.  **Efficiency:** It handles binary data (MsgPack) efficiently, keeping memory usage low even if the worker lags behind.
3.  **Simplicity:** I am already using Redis for caching. Using it for the queue avoids adding a new component (like Kafka) to my infrastructure.

### Implementation Details

1.  **Serialization:** Events are packed into **MsgPack** format to reduce memory footprint and network traffic.
2.  **Persistence:** Redis is configured with AOF (`appendfsync everysec`) to persist the stream to disk.
3.  **Capping:** The stream length is capped (`MAXLEN`) to prevent memory overflow during extended worker downtime.

## Consequences

### Positive

**Positive:** Decouples API from DB. Guarantees data safety for batches. easy to scale workers.

### Negative

**Negative:** Requires implementing a "Worker" service to manage stream reading and acknowledgments.
