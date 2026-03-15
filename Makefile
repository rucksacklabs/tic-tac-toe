# Purpose: Shortcut commands for common development tasks (migrations, linting, etc.).
# Architecture: Tooling/Automation.
# Notes: Simplifies Alembic migration commands and database setup.
.PHONY: help install run test format lint coverage clean migrate migration \
        docker-build docker-run helm-lint helm-template helm-install helm-upgrade helm-uninstall \
        openapi

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install     Install dependencies (uv sync)"
	@echo "  run         Run the API server (uvicorn, reload)"
	@echo "  test        Run tests with pytest"
	@echo "  format      Format code with ruff"
	@echo "  lint        Lint with ruff"
	@echo "  typecheck   Type-check with ty"
	@echo "  coverage    Run tests with coverage report"
	@echo "  clean       Remove cache and coverage artifacts"
	@echo "  openapi     Generate OpenAPI spec to openapi.json"
	@echo "  migrate     Apply all pending migrations"
	@echo "  migration   Generate a new migration (usage: make migration MSG='describe change')"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build   Build the Docker image (IMAGE_TAG=latest)"
	@echo "  docker-run     Run the container locally on port 8000"
	@echo ""
	@echo "Helm:"
	@echo "  helm-lint      Lint the Helm chart"
	@echo "  helm-template  Render Helm templates to stdout"
	@echo "  helm-install   Install the chart (ANTHROPIC_API_KEY required)"
	@echo "  helm-upgrade   Upgrade an existing release (ANTHROPIC_API_KEY required)"
	@echo "  helm-uninstall Uninstall the release"

install:
	uv sync

run:
	@set -a && . ./.env.local && set +a && uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

test:
	uv run pytest

format:
	uv run ruff format .

fmt:
	uv run ruff format .

lint:
	uv run ruff check .

check:
	uv run ruff format .
	uv run ruff check .
	uv run ty check app

typecheck:
	uv run ty check app

coverage:
	uv run pytest --cov=app --cov-report=term-missing

clean:
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage

migrate:  ## Apply all pending migrations
	@set -a && . ./.env.local && set +a && uv run alembic upgrade head

migration:  ## Generate a new migration (usage: make migration MSG="describe change")
	uv run alembic revision --autogenerate -m "$(MSG)"

IMAGE_TAG ?= latest
RELEASE_NAME ?= tic-tac-toe
HELM_CHART := helm

docker-build:
	docker build -t tic-tac-toe:$(IMAGE_TAG) .

docker-run:
	docker run --rm -p 8000:8000 \
		-e DATABASE_URL="$(DATABASE_URL)" \
		-e AI_COACH_MODEL="$(AI_COACH_MODEL)" \
		-e ANTHROPIC_API_KEY="$(ANTHROPIC_API_KEY)" \
		tic-tac-toe:$(IMAGE_TAG)

helm-lint:
	helm lint $(HELM_CHART)

helm-template:
	helm template $(RELEASE_NAME) $(HELM_CHART) \
		--set secret.anthropicApiKey="$(ANTHROPIC_API_KEY)"

helm-install:
	helm install $(RELEASE_NAME) $(HELM_CHART) \
		--set secret.anthropicApiKey="$(ANTHROPIC_API_KEY)"

helm-upgrade:
	helm upgrade $(RELEASE_NAME) $(HELM_CHART) \
		--set secret.anthropicApiKey="$(ANTHROPIC_API_KEY)"

helm-uninstall:
	helm uninstall $(RELEASE_NAME)

openapi:
	uv run python -c "import json; from main import app; print(json.dumps(app.openapi(), indent=2))" > openapi.json
	@echo "OpenAPI spec written to openapi.json"
