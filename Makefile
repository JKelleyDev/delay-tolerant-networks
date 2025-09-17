.PHONY: help install test coverage lint format clean all

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run unit tests"
	@echo "  coverage    - Run tests with coverage report (HTML + XML)"
	@echo "  lint        - Run linting checks"
	@echo "  format      - Format code with black"
	@echo "  typecheck   - Run type checking with mypy"
	@echo "  clean       - Clean up temporary files"
	@echo "  all         - Run format, lint, typecheck, and test"
	@echo "  dev-setup   - Set up development environment with pre-commit"
	@echo "  pre-commit  - Run pre-commit hooks on all files"

# Install dependencies
install:
	pip install -r requirements.txt

# Run unit tests
test:
	python -m pytest tests/ -v

# Run tests with coverage
coverage:
	python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml --cov-fail-under=80

# Run linting
lint:
	python -m flake8 src/ tests/

# Format code
format:
	python -m black src/ tests/

# Type checking
typecheck:
	python -m mypy src/

# Clean temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/

# Run all checks
all: format lint typecheck test

# Development setup
dev-setup: install
	pip install -r requirements-dev.txt
	pre-commit install
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify everything works."

# Run pre-commit on all files
pre-commit:
	pre-commit run --all-files