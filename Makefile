.PHONY: help install test lint format clean docker-up docker-down db-init

help:
	@echo "Available commands:"
	@echo "  install     Install dependencies"
	@echo "  test       Run tests"
	@echo "  lint       Run linting"
	@echo "  format     Format code"
	@echo "  docker-up  Start docker services"
	@echo "  docker-down Stop docker services"
	@echo "  db-init    Initialize database"

install:
	poetry install

test:
	poetry run pytest -v --cov=app --cov-report=html

test-fast:
	poetry run pytest -v --no-cov

lint:
	poetry run ruff check src/ tests/
	poetry run pre-commit run --all-files

format:
	poetry run ruff format src/ tests/
	poetry run ruff check --fix src/ tests/

docker-up:
	docker-compose up -d --build

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

db-init:
	poetry run python scripts/init_db.py

migrate:
	poetry run alembic upgrade head

pre-commit-install:
	poetry run pre-commit install

dev:
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .coverage htmlcov .pytest_cache

.PHONY: all
all: install lint test