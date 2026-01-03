# AICM Development Makefile
# Platform-aware commands for cross-platform development
# Per DISC-029: Cross-Platform Development Workflow Strategy

.PHONY: help dev test switch-out switch-in env docker-up docker-down lint clean

# Detect OS
UNAME := $(shell uname)
ifeq ($(UNAME), Darwin)
    PLATFORM := mac
else
    PLATFORM := docker
endif

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help:
	@echo ""
	@echo "$(CYAN)AICM Development Commands$(NC)"
	@echo "========================="
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make dev         - Start development server (platform-aware)"
	@echo "  make test        - Run tests (platform-aware)"
	@echo "  make lint        - Run linters"
	@echo ""
	@echo "$(GREEN)Machine Switching:$(NC)"
	@echo "  make switch-out  - Prepare to leave this machine"
	@echo "  make switch-in   - Arriving at this machine"
	@echo "  make env         - Show current environment"
	@echo ""
	@echo "$(GREEN)Docker (Win11):$(NC)"
	@echo "  make docker-up   - Start Docker containers"
	@echo "  make docker-down - Stop Docker containers"
	@echo "  make docker-logs - View backend logs"
	@echo "  make docker-shell- Shell into backend container"
	@echo ""
	@echo "$(YELLOW)Current platform: $(PLATFORM)$(NC)"
	@echo ""

# Environment detection
env:
	@python scripts/detect_env.py

# Development server (platform-aware)
dev:
ifeq ($(PLATFORM), mac)
	@echo "🍎 Starting Mac Native dev server on port 8100..."
	python -m uvicorn backend.main:app --reload --port 8100
else
	@echo "🪟 Starting Docker containers..."
	docker compose --profile main up
endif

# Run backend only (no frontend)
dev-backend:
ifeq ($(PLATFORM), mac)
	@echo "🍎 Starting Mac Native backend only..."
	python -m uvicorn backend.main:app --reload --port 8100
else
	@echo "🪟 Starting Docker backend only..."
	docker compose --profile main up aidev-backend aidev-phoenix
endif

# Run tests (platform-aware)
test:
ifeq ($(PLATFORM), mac)
	@echo "🍎 Running tests natively..."
	python -m pytest tests/ -v --tb=short
else
	@echo "🪟 Running tests in Docker..."
	docker exec aidev-backend pytest tests/ -v --tb=short
endif

# Quick test (fail fast)
test-quick:
ifeq ($(PLATFORM), mac)
	python -m pytest tests/ -x -q
else
	docker exec aidev-backend pytest tests/ -x -q
endif

# Machine switching
switch-out:
	@./scripts/switch_out.sh

switch-in:
	@git pull origin $$(git branch --show-current)
	@./scripts/switch_in.sh

# Docker commands (primarily for Win11)
docker-up:
	docker compose --profile main up -d

docker-down:
	docker compose --profile main down

docker-logs:
	docker logs -f aidev-backend

docker-shell:
	docker exec -it aidev-backend /bin/bash

docker-rebuild:
	docker compose --profile main build --no-cache
	docker compose --profile main up -d

# Linting
lint:
ifeq ($(PLATFORM), mac)
	python -m ruff check backend/ scripts/ src/
else
	docker exec aidev-backend ruff check backend/ scripts/ src/
endif

# Format code
format:
ifeq ($(PLATFORM), mac)
	python -m ruff format backend/ scripts/ src/
else
	docker exec aidev-backend ruff format backend/ scripts/ src/
endif

# Clean temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

# Install dependencies (Mac native)
install:
ifeq ($(PLATFORM), mac)
	pip install -r backend/requirements.txt
	pip install -r backend/requirements-heavy.txt
else
	@echo "On Docker, rebuild container: make docker-rebuild"
endif

# Status check
status:
	@echo ""
	@echo "$(CYAN)Git Status:$(NC)"
	@git status --short
	@echo ""
	@echo "$(CYAN)Current Branch:$(NC) $$(git branch --show-current)"
	@echo "$(CYAN)Last Commit:$(NC) $$(git log -1 --pretty=format:'%h %s')"
	@echo ""
ifeq ($(PLATFORM), docker)
	@echo "$(CYAN)Docker Containers:$(NC)"
	@docker ps --filter "name=aidev" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker not running"
endif
