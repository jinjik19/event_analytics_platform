.PHONY: help start stop restart logs lint format analyze test test-unit test-e2e test-cov load-realistic load-stress seed-start seed-stop
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
