.PHONY: help start stop restart logs lint format analyze test test-unit test-e2e test-cov load-realistic load-stress seed-start seed-stop debezium-register debezium-status debezium-topics logs-debezium dbt-debug dbt-run dbt-test dbt-docs dbt-freshness dbt-build airflow-start airflow-stop airflow-restart airflow-logs
APP_ENV_TEST=test

# Default target
help:
	@echo "Available commands:"
	@echo "  start      - Start containers (detached)"
	@echo "  stop       - Stop containers"
	@echo "  restart    - Restart containers"
	@echo "  logs-app   - Tail logs for the app"
	@echo "  lint       - Check code style"
	@echo "  format     - Format code"
	@echo "  analyze    - Run full static analysis"

# Docker
start:
	@if [ ! -f .env ]; then echo ".env file not found! Copy .env.example to .env"; exit 1; fi
	docker-compose up -d --build

stop:
	docker-compose down

clean:
	docker-compose down -v

restart: stop start

logs-%:
	docker-compose logs -f event_analytics_$*

# Seeder
seed-start:
	docker-compose --profile seeder up -d seeder

seed-stop:
	docker-compose stop seeder
	docker-compose rm -f seeder

# CDC / Debezium
clickhouse-migrate:
	docker exec -i event_analytics_dwh clickhouse-client \
		--user $(shell grep ^DWH_USER .env | cut -d= -f2) \
		--password $(shell grep ^DWH_PASSWORD .env | cut -d= -f2) \
		--multiquery < configs/clickhouse/init/02_kafka_cdc.sql

debezium-register:
	@bash configs/debezium/register.sh

debezium-status:
	@curl -s http://localhost:8083/connectors/postgres-cdc/status | python3 -m json.tool

debezium-topics:
	@docker exec redpanda rpk topic list

logs-debezium:
	docker-compose logs -f debezium

# Quality Assurance
lint:
	uv run ruff check src/

format:
	uv run ruff format src/
	uv run ruff check --fix src/

analyze:
	@echo "Running Ruff (Linter & Security)..."
	@uv run ruff check src/
	@echo "Ruff passed"

	@echo "Running MyPy (Types)..."
	@uv run mypy src/
	@echo "MyPy passed"

# Tests

test:
	APP_ENV=$(APP_ENV_TEST) uv run pytest tests -v

test-unit:
	APP_ENV=$(APP_ENV_TEST) uv run pytest tests/unit -v

test-integrations:
	APP_ENV=$(APP_ENV_TEST) uv run pytest tests/integrations -v

test-cov:
	APP_ENV=$(APP_ENV_TEST) uv run pytest --cov=src tests

# dbt
DBT_DIR=orchestrator/include/event_analytics_dbt

dbt-build:
	cd $(DBT_DIR) && uv run --env-file ../../../.env dbt build

dbt-debug:
	cd $(DBT_DIR) && uv run --env-file ../../../.env dbt debug

dbt-run:
	cd $(DBT_DIR) && uv run --env-file ../../../.env dbt run

dbt-test:
	cd $(DBT_DIR) && uv run --env-file ../../../.env dbt test

dbt-docs:
	cd $(DBT_DIR) && uv run --env-file ../../../.env dbt docs generate && uv run --env-file ../../../.env dbt docs serve --port 18080

dbt-freshness:
	cd $(DBT_DIR) && uv run --env-file ../../../.env dbt source freshness

# Airflow (Astronomer CLI)
airflow-start:
	cd orchestrator && astro dev start

airflow-stop:
	cd orchestrator && astro dev stop

airflow-restart:
	cd orchestrator && astro dev restart

airflow-logs:
	cd orchestrator && astro dev logs

airflow-test:
	cd orchestrator && astro dev pytest tests/

# Load Tests

load-realistic-%:
	@mkdir -p tests/load/results
	uv run locust -f tests/load/locustfile.py \
		--host=http://localhost:8000 \
		--headless \
		-u 1000 \
		-r 50 \
		-t 5m \
		--csv=tests/load/results/benchmark_stage$* \
		--html=tests/load/results/benchmark_stage$*.html \
		MixedLoadUser

load-stress:
	@mkdir -p tests/load/results
	uv run locust -f tests/load/locustfile.py \
		--host=http://localhost:8000 \
		--headless \
		-u 500 \
		-r 50 \
		-t 3m \
		--csv=tests/load/results/stress_limit \
		--html=tests/load/results/stress_limit.html \
		StressBatchUser
