.PHONY: help install install-dev run-api run-agent run-mcp config-check clean lint format test

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

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build dist .pytest_cache .mypy_cache .ruff_cache
	@echo "Clean complete"
