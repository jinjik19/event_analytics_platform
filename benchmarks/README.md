# 📊 Performance Benchmarks History

This directory contains detailed performance reports for each architectural stage of the Event Analytics Platform.

## Summary

| Stage       | Architecture               | Max Throughput    | Latency (p99) | Status  | Report                                    |
| ----------- | -------------------------- | ----------------- | ------------- | ------- | ----------------------------------------- |
| **Stage 1** | Sync (FastAPI -> Postgres) | **~913 events/s** | 260ms         | ✅ Done | [View Report](./stage1_sync_ingestion.md) |

## Methodology

We use **Locust** for load generation.

- **Hardware:** MacBook Pro M3 (Docker Desktop)
- **Database:** PostgreSQL 17 (default config)
- **Load Profile:** Realistic E-commerce Funnel (MixedLoadUser)
