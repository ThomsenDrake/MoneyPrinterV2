.PHONY: help install test lint format type-check quality clean all

# Default target
help:
	@echo "AutoMuse - Development Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  make install      - Install all dependencies (including dev dependencies)"
	@echo "  make test         - Run all tests with coverage"
	@echo "  make test-unit    - Run only unit tests"
	@echo "  make lint         - Run flake8 linter"
	@echo "  make format       - Format code with Black"
	@echo "  make format-check - Check code formatting without modifying"
	@echo "  make type-check   - Run mypy type checker"
	@echo "  make quality      - Run all quality checks (lint + type-check + test)"
	@echo "  make clean        - Remove build artifacts and cache files"
	@echo "  make all          - Format code and run all quality checks"

# Install dependencies
install:
	pip install --upgrade pip
	pip install -r requirements.txt

# Run all tests with coverage
test:
	pytest tests/

# Run only unit tests
test-unit:
	pytest tests/ -m unit

# Run linting with flake8
lint:
	@echo "Running flake8..."
	flake8 src/ tests/

# Format code with Black
format:
	@echo "Formatting code with Black..."
	black src/ tests/
	@echo "Sorting imports with isort..."
	isort src/ tests/

# Check formatting without modifying
format-check:
	@echo "Checking code formatting..."
	black --check src/ tests/
	isort --check-only src/ tests/

# Run type checking with mypy
type-check:
	@echo "Running mypy type checker..."
	mypy src/

# Run all quality checks
quality: lint type-check test
	@echo "✓ All quality checks passed!"

# Format and run quality checks
all: format quality
	@echo "✓ Code formatted and all checks passed!"

# Clean build artifacts and cache
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf build/ dist/ htmlcov/ .coverage coverage.xml
	@echo "✓ Cleaned!"
