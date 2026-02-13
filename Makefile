.PHONY: help up down restart logs test test-backend test-frontend lint lint-backend lint-frontend shell-backend shell-frontend clean rebuild

# Default target
help:
	@echo "fglInterpreter Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Service Management:"
	@echo "  make up              - Start all services"
	@echo "  make down            - Stop all services"
	@echo "  make restart         - Restart all services"
	@echo "  make logs            - View logs (all services)"
	@echo "  make logs-backend    - View backend logs"
	@echo "  make logs-frontend   - View frontend logs"
	@echo ""
	@echo "Testing:"
	@echo "  make test            - Run all tests"
	@echo "  make test-backend    - Run backend tests"
	@echo "  make test-frontend   - Run frontend tests"
	@echo "  make coverage        - Run tests with coverage"
	@echo ""
	@echo "Linting:"
	@echo "  make lint            - Run all linters"
	@echo "  make lint-backend    - Run backend linters (Black + Ruff)"
	@echo "  make lint-frontend   - Run frontend linter (ESLint)"
	@echo "  make format          - Auto-format all code"
	@echo ""
	@echo "Development:"
	@echo "  make shell-backend   - Open shell in backend container"
	@echo "  make shell-frontend  - Open shell in frontend container"
	@echo "  make rebuild         - Rebuild and restart services"
	@echo "  make clean           - Remove all containers, volumes, and images"
	@echo ""

# Service Management
up:
	docker compose up -d
	@echo "Services started!"
	@echo "Frontend: http://localhost:5173"
	@echo "Backend: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/api/docs"

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-frontend:
	docker compose logs -f frontend

# Testing
test: test-backend test-frontend

test-backend:
	docker compose exec backend pytest tests/unit -v

test-frontend:
	docker compose exec frontend npm test -- --run

coverage:
	docker compose exec backend pytest tests/unit --cov=fglinterpreter --cov-report=term-missing

# Linting
lint: lint-backend lint-frontend

lint-backend:
	docker compose exec backend black --check .
	docker compose exec backend ruff check .

lint-frontend:
	docker compose exec frontend npm run lint

format:
	docker compose exec backend black .
	docker compose exec backend ruff check --fix .
	docker compose exec frontend npm run lint -- --fix

# Development
shell-backend:
	docker compose exec backend bash

shell-frontend:
	docker compose exec frontend sh

rebuild:
	docker compose down
	docker compose build --no-cache
	docker compose up -d

clean:
	docker compose down -v
	docker system prune -f

# Build
build:
	docker compose build

# Status
status:
	docker compose ps
