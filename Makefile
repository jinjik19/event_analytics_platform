.PHONY: help start stop restart logs lint format analyze


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
