# Event Analytics Platform

![Python 3.13](https://img.shields.io/badge/python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128.0-005571?style=flat-square&logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**A high-performance, self-hosted event analytics platform.**
Designed to handle real-time ingestion, processing, and visualization of user behavior data. Built to evolve from a simple API to a distributed event-driven system.

> The goal is to build a scalable pipeline comparable to Mixpanel/Amplitude but open-source.

---

## Architecture

![container](./docs/architecture/stage1/container.drawio.png)

_Detailed architecture breakdown:_

- [Stage 1](./docs/architecture/stage1/)

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

[] Stage 1: Backend Foundation

    [x] Clean Architecture, DI, UoW.

    [x] High-performance Batch Ingestion (asyncpg + executemany).

    [x] Fail-safe validation strategy.

    [ ] Async Processing

    [ ] Load Testing benchmarks (Locust).

[ ] Stage 2: CDC & OLAP

[ ] Stage 3: Orchestration & Quality

[ ] Stage 4: Production Deploy (VPS)

[ ] Stage 5: Kubernetes

[ ] Stage 6: Cloud Migration

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
curl http://localhost:8000/healthz
# Output: {"status": "ok"}
```

4. Create/Run migration (optional, because migrations apply with docker containers up)

Create migration.

1. Create sql file with your command in db/schema/postgres
2. Run command

```bash
atlas migrate diff some_name --env postgres
```

Run migration

```bash
atlas migrate apply --env postgres
```

5. OpenAPI/Swagger - http://localhost:8000/docs#/

---

📝 License

This project is licensed under the MIT License.
