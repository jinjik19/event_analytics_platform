# 3. Use Atlas for Database Migrations

Date: 2026-01-09
Status: Accepted

## Context

The platform relies on `asyncpg` for high-performance asynchronous database interactions with PostgreSQL.

The standard Python migration tool, **Alembic**, requires **SQLAlchemy** as a core dependency. Since our application does not use an ORM, including SQLAlchemy solely for migrations introduces significant downsides:

1.  **Dependency Bloat:** Increases Docker image size and installation time.
2.  **Maintenance Overhead:** Requires managing versions of a complex library that is not used in runtime logic.
3.  **Coupling:** Ties database schema management to the Python environment.

I need a language-agnostic, lightweight, and modern tool to manage database schema lifecycle effectively.

## Decision

I will use **Atlas** (AtlasGO) as the database schema management tool.

I will adopt the **Declarative Workflow** (Infrastructure-as-Code approach):

1.  The desired database state is defined in HCL or SQL schema files.
2.  Atlas automatically calculates the difference between the desired state and the actual database.
3.  Atlas generates and applies the necessary SQL migration plans.

## Consequences

### Positive

- **Decoupling:** Database management is separated from the application code and Python dependencies. The migration tool is a single binary.
- **Declarative Schema:** The schema definition serves as the "source of truth" and documentation, which is easier to read than a chain of migration scripts.
- **Safety & Linting:** Atlas provides built-in migration linting (e.g., detecting destructive changes like dropping columns) and CI/CD integration.
- **Leaner Containers:** Removing SQLAlchemy reduces the Docker image size and attack surface.

### Negative

- **Learning Curve:** I needs to learn the Atlas CLI and workflow, which differs from the standard Python/Alembic ecosystem.
- **Complex Data Migrations:** While Atlas handles _schema_ changes perfectly, complex _data_ migrations (e.g., iterating over rows and transforming data using Python logic) might require separate scripts or a hybrid approach.
