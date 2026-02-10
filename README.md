# Event Analytics Platform

![Python 3.13](https://img.shields.io/badge/python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128.0-005571?style=flat-square&logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**A high-performance, self-hosted event analytics platform.**
Designed to handle real-time ingestion, processing, and visualization of user behavior data. Built to evolve from a simple API to a distributed event-driven system.

> The goal is to build a scalable pipeline comparable to Mixpanel/Amplitude but open-source.

---

## Architecture

```mermaid
flowchart LR
    %% Styles
    classDef storage fill:#3f51b5,stroke:#fff,stroke-width:2px,color:#fff;
    classDef service fill:#2d3436,stroke:#fff,stroke-width:2px,color:#fff;
    classDef monitor fill:#00b894,stroke:#fff,stroke-width:2px,color:#fff;
    classDef dead fill:#d63031,stroke:#333,stroke-width:2px,color:#fff;

    %% Input
    User((User / Seeder)) -->|HTTP POST| API[API Gateway]:::service

    %% Main Data Flow
    subgraph "Data Pipeline"
        API -->|1. Ingest| Stream[(Redis Stream)]:::storage
        Stream -->|2. Read Group| Worker[Worker Service]:::service
        Worker -->|3. Write Batch| DB[(PostgreSQL)]:::storage
    end

    %% Error Handling
    Worker -.->|4. Error DLQ| DLQ[(Events DLQ Stream)]:::dead

    %% Observability
    subgraph "Observability Stack"
        Prometheus[Prometheus]:::monitor
        Grafana[Grafana]:::monitor

        Prometheus -->|Query| Grafana
    end

    %% Metrics Scraping
    API -.->|/metrics| Prometheus
    Worker -.->|/metrics| Prometheus

    %% Link Styling
    linkStyle 4 stroke:#d63031,stroke-width:2px,stroke-dasharray: 5 5;
    linkStyle 6,7 stroke:#00b894,stroke-width:2px,stroke-dasharray: 5 5;
```

- [architecture](./docs/architecture/)

---

## Tech Stack

### **Core**

![Python 3.13](https://img.shields.io/badge/python_3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Pydantic V2](https://img.shields.io/badge/Pydantic_v2-e92063?style=for-the-badge&logo=pydantic&logoColor=white)

### **Streaming & Storage:**

![PostgreSQL](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)

### **Infrastructure:**

![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

### **Migrations**

![Atlas](https://img.shields.io/badge/Atlas-2080F0?style=for-the-badge&logo=go&logoColor=white)

---

## Roadmap & Progress

- [x] **Stage 1: Backend Foundation**
  - [x] Clean Architecture, DI (Dishka), UoW.
  - [x] High-performance Batch Ingestion (asyncpg + executemany).
  - [x] Fail-safe validation strategy (Pydantic v2).
  - [x] Structured Logging & Metrics preparation.
  - [x] Load Testing benchmarks ([View Results](./benchmarks/stage1_sync_ingestion.md)).

- [/] **Stage 2: Async Processing** (Current Focus)
  - [x] Decouple API from DB using Redis Streams.
  - [x] Background Workers implementation.
  - [x] At-least-once delivery guarantees.
  - [ ] Load Testing benchmarks ([View Results]()).

- [ ] **Stage 3: CDC & OLAP**
  - [ ] ClickHouse setup.
  - [ ] Debezium & Kafka (CDC).
  - [ ] Migration data from Postgre to Clickhouse

- [ ] **Stage 4: Orchestration & Quality**

- [ ] **Stage 5: Production Deploy (VPS)**

- [ ] **Stage 6: Kubernetes**

- [ ] **Stage 7: Cloud Migration (AWS/GCP)**

---

## Getting Started

### Prerequisites

- Python 3.13+
- Docker & Docker Compose

### Installation

1. Clone the repository

```bash
git clone https://github.com/jinjik19/event_analytics_platform.git
cd event_analytics_platform/
```

2. Run the API Server

```bash
# Start all services
make start
# OR
docker-compose up -d --build
```

3. Check Health

```bash
curl http://localhost:8000/health
# Output: {"status": "ok"}
```

Prometheus Targets - http://localhost:9090/targets
Grafana - http://localhost:3000

4. Create/Run migration (optional, because migrations apply with docker containers up)

#### Create migration.

1. Create sql file with your command in db/schema/postgres
2. Run command

```bash
atlas migrate diff some_name --env postgres
```

#### Run migration

```bash
atlas migrate apply --env postgres
```

5. OpenAPI/Swagger - http://localhost:8000/docs#/

---

### Additional utils

1. Seed

#### Run seed

```bash
make seed-start
```

#### Stop seed

```bash
make seed-stop
```

2. Load Tests

Information about load test [load_tests](./tests/load/README.md)

---

📝 License

This project is licensed under the MIT License.
