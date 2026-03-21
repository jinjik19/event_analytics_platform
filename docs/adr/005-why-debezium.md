# 5. Use Debezium for Change Data Capture (CDC)

Date: 2026-03-04
Status: Accepted

## Context

The event analytics platform requires reliable synchronization of data from the primary OLTP database (PostgreSQL) into downstream systems used for analytics and processing.

The architecture must ensure:

1. **Low Impact on the Database:** Data extraction should not add significant load to the production database.
2. **Reliability:** Changes must not be lost even if downstream systems fail.
3. **Near Real-Time Processing:** Updates in the database should appear in the streaming system with minimal delay.
4. **Scalability:** The solution must support future growth in data volume.

I evaluated several options:

- **Polling (SELECT with updated_at):** Simple but inefficient. Polling increases database load and may miss rapid updates.
- **Custom WAL reader:** Possible but complex to implement and maintain.
- **Managed CDC services (e.g., AWS DMS):** Adds vendor lock-in and operational cost.
- **Debezium:** Mature open-source CDC platform built specifically for this use case.

## Decision

I decided to use **Debezium** for Change Data Capture.
Debezium will read changes directly from the **PostgreSQL Write-Ahead Log (WAL)** and publish them as events to the streaming platform.

Pipeline:
PostgreSQL
 ↓
Debezium
 ↓
Redpanda topics
 ↓
Consumers
(analytics, ETL, processing services)

### Why Debezium?

1. **Log-Based CDC:** Debezium reads database transaction logs instead of polling tables, minimizing database load.
2. **Reliability:** Uses PostgreSQL replication slots to ensure no events are lost.
3. **Near Real-Time Streaming:** Changes appear in the event stream almost immediately after they are committed.
4. **Integration:** Works natively with Kafka-compatible platforms such as Redpanda.

### Implementation Details

1. **Connector:** PostgreSQL connector running through Kafka Connect.
2. **Replication Slot:** Used to track WAL consumption.
3. **Event Format:** Debezium change events containing `before`, `after`, and operation type (`c`, `u`, `d`).
4. **Topic Naming:** Events are published using the pattern `server.database.table`.

## Consequences

### Positive

**Positive:** Reliable CDC pipeline with near real-time updates. Minimal load on the primary database. Strong integration with streaming ecosystems.

### Negative

**Negative:** Adds operational complexity due to the need to maintain Kafka Connect and Debezium connectors.
