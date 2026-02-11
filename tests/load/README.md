# Load Testing for Event Analytics Platform

## Contents

- [Overview](#overview)
- [When to Use Load Testing](#when-to-use-load-testing)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Test Scenarios](#test-scenarios)
- [Testing Against Staging/Production](#testing-against-stagingproduction)
- [Benchmarks & Goals](#benchmarks-and-goals)
- [Determining Load Capacity](#determining-load-capacity)
- [Rate Limit Testing](#rate-limit-testing)
- [Troubleshooting](#troubleshooting)
- [Historical Benchmarks](../../benchmarks/README.md)

---

## Overview

Load tests are implemented using [Locust](https://locust.io/) - a modern Python framework for load testing.

### Test Structure

| User Class       | Purpose                  | Weight |
| ---------------- | ------------------------ | ------ |
| `MixedLoadUser`  | Realistic mixed workload | 100    |
| `StressTestUser` | Extreme load testing     | 10     |

### Projects Created

Load tests automatically create 4 projects with different rate limits:

| Plan       | Count | Rate Limit |
| ---------- | ----- | ---------- |
| FREE       | 1     | 100 RPM    |
| PRO        | 2     | 1000 RPM   |
| ENTERPRISE | 1     | 10000 RPM  |

API keys are randomly selected during tests to verify rate limiting works correctly.

---

## When to Use Load Testing

Load testing is **NOT for CI/CD pipelines**. It's for:

1. **Capacity Planning** - Determine if your infrastructure can handle expected load
2. **Before Production Deployment** - Verify new configuration handles required RPS
3. **After Infrastructure Changes** - Validate database upgrades, new servers, etc.
4. **Finding Bottlenecks** - Identify what breaks first under load
5. **Rate Limit Validation** - Verify rate limiting works correctly per plan

### Where to Run Load Tests

| Environment         | Purpose                                               |
| ------------------- | ----------------------------------------------------- |
| **Local**           | Development, initial testing                          |
| **Staging**         | Pre-production validation with production-like config |
| **Production-like** | Dedicated environment mirroring production            |

**Never run stress tests against production** - use a staging environment with identical configuration.

---

## Installation

### 1. Install dependencies

```bash
uv sync --group dev
```

### 2. Configure environment

```bash
# Token for creating projects (must match SECRET_TOKEN on server)
export SECRET_TOKEN="your-secret-token"

# Optional: use existing API key (skips project creation)
export LOAD_TEST_API_KEY="wk_dev_your_existing_key1,wk_dev_your_existing_key1"

# Optional: project name prefix
export PROJECT_NAME_PREFIX="load_test"
```

### 3. Start the server

```bash
# Local development
make start

# OR
docker-compose up -d
```

---

## Quick Start

### Web UI Mode (recommended)

```bash
uv run locust -f tests/load/locustfile.py --host=http://localhost:8000

# Open http://localhost:8089 in browser
```

In web interface:

1. Set number of users
2. Set spawn rate (users/sec)
3. Click "Start swarming"
4. Watch real-time charts

### Headless Mode

```bash
uv run locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --headless \
    -u 50 \
    -r 10 \
    -t 5m \
    --csv=tests/load/results/test
```

---

## Test Scenarios

### 1. Smoke Test (basic validation)

```bash
uv run locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --headless \
    -u 5 \
    -r 1 \
    -t 30s \
    MixedLoadUser
```

### 2. Realistic Benchmark

```bash
uv run locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --headless \
    -u 100 \
    -r 5 \
    -t 5m \
    --csv=tests/load/results/benchmark_stage \
    --html=tests/load/results/benchmark_report.html \
    MixedLoadUser
```

### 3. Stress Test (finding breaking point)

```bash
# Run against staging only!
uv run locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --headless \
    -u 50 \
    -r 5 \
    -t 3m \
    --csv=tests/load/results/stress_limit \
    --html=tests/load/results/stress_limit.html
    StressBatchUser
```

---

## Testing Against Staging/Production

### Staging Environment Testing

Test your staging environment to validate production configuration:

```bash
# 1. Set staging credentials
export SECRET_TOKEN="staging-secret-token"
# OR set existing keys to avoid creating projects
export LOAD_TEST_API_KEYS="wk_staging_1,wk_staging_2"

# 2. Run capacity test (using Realistic User)
uv run locust -f tests/load/locustfile.py \
    --host=[https://staging-api.example.com](https://staging-api.example.com) \
    --headless \
    -u 100 \
    -r 10 \
    -t 30m \
    --csv=tests/load/results/staging_capacity \
    MixedLoadUser
```

### What to Validate

Before production deployment, verify:

| Check                        | Command                                | Target                    |
| ---------------------------- | -------------------------------------- | ------------------------- |
| Normal Traffic (RPS check)   | `MixedLoadUser -u 100`                 | 0% errors, <200ms P95     |
| Database Writes (Throughput) | `StressBatchUser -u 50`                | No 500 errors, stable RAM |
| Specific Scenarios           | MixedLoadUser --tags purchase          | Check conversion funnel   |
| Rate Limits                  | Check logic manually or via unit tests | 429 for FREE plan         |

### Distributed Testing (multiple machines)

For high load testing, run Locust in distributed mode:

```bash
# Master node
uv run locust -f tests/load/locustfile.py \
    --host=https://staging:8000 \
    --master

# Worker nodes (run on multiple machines/pods)
uv run locust -f tests/load/locustfile.py \
    --worker \
    --master-host=<master-ip-address>
```

---

## Benchmarks and Goals

### Performance Evolution Roadmap

As the architecture evolves, our performance targets shift from raw functionality to massive scale and analytical speed.

| Metric           | **Stage 1** (Sync) | **Stage 2** (Async) | **Stage 3** (CDC + OLAP) | **Stage 6** (K8s)   | **Stage 7** (Cloud) |
| ---------------- | ------------------ | ------------------- | ------------------------ | ------------------- | ------------------- |
| **Architecture** | Monolith API -> PG | API -> Redis -> PG  | + Kafka -> ClickHouse    | Microservices (HPA) | AWS/GCP Managed     |
| **Throughput**   | **1K** events/s    | **5K** events/s     | **10K** events/s         | **50K+** events/s   | **100K+** events/s  |
| **Ingest P99**   | < 200ms            | < **50ms**          | < 50ms                   | < 50ms              | < 50ms              |
| **Query P99**    | N/A (Slow)         | N/A                 | < **200ms**              | < 100ms             | < 100ms (Cluster)   |
| **Data Loss**    | 0%                 | 0% (At-least-once)  | 0%                       | 0%                  | 0%                  |
| **Bottleneck**   | DB I/O             | Worker Speed        | Network / Disk           | Cost                | Wallet ($$)         |

### How to Calculate Throughput

Locust shows HTTP requests, not business events. To get real throughput:

1. **Single Events:** 1 Request = 1 Event.
2. **Batches:** 1 Request ≈ 20 Events (avg batch size).

**Formula:**
$$Throughput \approx (RPS_{single} \times 1) + (RPS_{batch} \times 20)$$

### Example Interpretation

```text
Type    Name                                 req/s   Median   95%
-----------------------------------------------------------------
POST    /api/v1/event (Page View)            50.0    20ms     45ms  <- 50 events/s
POST    /api/v1/event/batch (mixed)          40.0    150ms    300ms <- ~800 events/s (40*20)
-----------------------------------------------------------------
Aggregated                                   90.0                   <- Total: ~850 events/s
```

### Save Reports

```bash
uv run locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --headless \
    -u 100 -r 10 -t 5m \
    --csv=tests/load/results/baseline \
    --html=tests/load/results/benchmark_stage.html \
    MixedLoadUser
```

> Open benchmark_stage.html in your browser to see RPS and Latency graphs over time.

---

## Determining Load Capacity

#### 1. Finding Average Sustainable Load

To get statistically significant data, we ignore the warmup period:

1. Run test with constant load for 10+ minutes.
2. Exclude first 60 seconds (warmup).
3. Analyze the stable period.

```bash
uv run locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --headless -u 50 -r 50 -t 10m \
    --csv=tests/load/results/baseline \
    MixedLoadUser
```

### Analysis Script (Python + Pandas):

```python
import pandas as pd

# Load history CSV generated by Locust
df = pd.read_csv('tests/load/results/baseline_stats_history.csv')

# Filter out the first 60 seconds of warmup
stable = df[df['Timestamp'] > df['Timestamp'].min() + 60]

# Calculate real RPS (Requests per Second)
avg_rps = stable['Total Request Count'].diff().mean()
avg_latency = stable['Total Average Response Time'].mean()

print(f"Average RPS: {avg_rps:.2f}")
print(f"Average Response Time: {avg_latency:.2f}ms")
```

#### 2. Finding Maximum Load (Breaking Point)

Use the Locust Web UI for a "Step Load" pattern: 1. Start with 10 users. 2. Every 2 minutes add 20 users. 3. Stop when: - Response time spikes exponentially (knee of the curve). - Error rate > 1%. - RPS stops growing despite adding users.

### 3. Capacity Formula

A quick way to estimate how many concurrent users your system can support:

```
Max RPS ≈ Concurrent Users / Avg Response Time (seconds)

Example:
- 100 concurrent users
- 50ms avg response = 0.05s(50ms)
- Max RPS = 100 / 0.05 = 2000 RPS
```

---

## Rate Limit Testing

Tests create projects with different plans to verify rate limiting:

| Plan       | Rate Limit | Expected Behavior |
| ---------- | ---------- | ----------------- |
| FREE       | 100 RPM    | 429 when exceeded |
| PRO        | 1000 RPM   | 429 when exceeded |
| ENTERPRISE | 10000 RPM  | 429 when exceeded |

### Verify Rate Limits

Run with high user count to trigger rate limits:

```bash
# Ensure you are using a FREE plan API key
export LOAD_TEST_API_KEY="wk_free_project_key"

uv run locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --headless \
    -u 200 \
    -r 50 \
    -t 5m \
    SingleEventUser
```

Watch for 429 responses in the output. FREE plan projects should hit rate limits first.

---

## Troubleshooting

| Symptom            | Probable Cause                  | Fix                                                         |
| ------------------ | ------------------------------- | ----------------------------------------------------------- |
| All Requests 401   | Invalid API Key or Secret Token | Check .env matches docker-compose.yml. Verify keys via curl |
| All Requests 429   | Rate Limit Triggered            | Reduce users (-u) or use ENTERPRISE plan keys               |
| High Latency (>1s) | Database Bottleneck             | Check CPU/Memory                                            |
| Connection Errors  | OS Socket Limit                 | Increase limit: ulimit -n 10000 (Linux/Mac)                 |
| Locust CPU High    | Python Generator Overhead       | Use fast_uuid (implemented) or Distributed Mode             |

### How to debug 401s

```bash
# Verify project creation works:
curl -X POST http://localhost:8000/api/v1/project \
  -H "Authorization: Bearer $SECRET_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "debug_test", "plan": "FREE"}'
```

---
