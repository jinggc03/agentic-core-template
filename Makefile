.PHONY: help install install-dev run-api run-agent run-mcp config-check clean lint format test check-supabase-cli supabase-start supabase-stop supabase-reset supabase-migrate supabase-status

help:
	@echo "Personal Agent Runtime - Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install dependencies"
	@echo "  make install-dev    Install with dev dependencies"
	@echo ""
	@echo "Running:"
	@echo "  make run-api        Run FastAPI server"
	@echo "  make run-agent      Run agent CLI"
	@echo "  make run-mcp        Run MCP server"
	@echo ""
	@echo "Configuration:"
	@echo "  make config-check   Check configuration (masked secrets)"
	@echo ""
	@echo "Development:"
	@echo "  make lint           Run linter (ruff)"
	@echo "  make format         Format code (ruff)"
	@echo "  make test           Run tests (pytest)"
	@echo "  make clean          Clean build artifacts"
	@echo ""
	@echo "Supabase:"
	@echo "  make supabase-start   Start local Supabase stack"
	@echo "  make supabase-stop    Stop local Supabase stack"
	@echo "  make supabase-reset   Reset local DB and apply migrations"
	@echo "  make supabase-migrate Push migrations to linked project"
	@echo "  make supabase-status  Show local Supabase status"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

run-api:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-agent:
	@echo "Agent CLI not yet implemented"

run-mcp:
	@echo "MCP server not yet implemented"

config-check:
	python scripts/config-check.py

lint:
	ruff check app tests

format:
	ruff format app tests
	ruff check app tests --fix

test:
	pytest tests -v

check-supabase-cli:
	@command -v supabase >/dev/null 2>&1 || (echo "Supabase CLI not found. Install it from https://supabase.com/docs/guides/cli/getting-started or use npx supabase." && exit 1)

supabase-start: check-supabase-cli
	supabase start

supabase-stop: check-supabase-cli
	supabase stop

supabase-reset: check-supabase-cli
	supabase db reset

supabase-migrate: check-supabase-cli
	supabase db push

supabase-status: check-supabase-cli
	supabase status

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build dist .pytest_cache .mypy_cache .ruff_cache
	@echo "Clean complete"
