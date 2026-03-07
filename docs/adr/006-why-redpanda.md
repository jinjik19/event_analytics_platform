# 6. Use Redpanda as the Event Streaming Platform

Date: 2026-03-04
Status: Accepted

## Context

The architecture requires a streaming platform to transport events between services and support CDC pipelines.

The system must support:

1. **High Throughput:** The platform must handle continuous event streams from the ingestion API and CDC pipeline.
2. **Reliability:** Events must be persisted and recoverable after failures.
3. **Scalability:** The system should support partitioned topics and horizontal scaling.
4. **Developer Simplicity:** As a solo developer project, the infrastructure should remain easy to operate locally and in production.

I evaluated the following options:

- **Redis Streams:** Good for lightweight queues, but less suitable for large-scale streaming and long-term event storage.
- **Apache Kafka:** Industry standard for streaming systems, but requires more operational overhead.
- **Cloud Streaming Services (Kinesis, Pub/Sub):** Introduces vendor lock-in and additional costs.
- **Redpanda:** Kafka-compatible streaming platform with simplified operations.

## Decision

I decided to use **Redpanda** as the event streaming platform.
Redpanda will serve as the central event bus for the system.

Pipeline:
Event Producers (API / Debezium)
 ↓
Redpanda Topics
 ↓
Consumers (workers, analytics services)

### Why Redpanda?

1. **Kafka API Compatibility:** Allows using existing Kafka tools and connectors such as Debezium.
2. **Operational Simplicity:** Redpanda does not require Zookeeper and is easier to deploy.
3. **Local Development:** Simple Docker-based deployment works well for a solo developer environment.

### Implementation Details

1. **Topics:** Used for event streams such as `events`, `cdc.users`, or `analytics.events`.
2. **Partitions:** Used to scale consumers and improve throughput.
3. **Consumers:** Worker services consume events using consumer groups.
4. **Persistence:** Redpanda stores events on disk to ensure durability.

## Consequences

### Positive

**Positive:** Scalable and reliable event streaming platform with strong integration with CDC tools.

### Negative

**Negative:** Adds another infrastructure component that must be monitored and maintained.
