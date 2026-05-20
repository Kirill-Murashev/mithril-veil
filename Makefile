.PHONY: install install-gliner lint format test test-integration compile check run-api clean build

PYTHON ?= python3
PIP := $(PYTHON) -m pip

install:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

install-gliner:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev,gliner]"

lint:
	ruff check app tests

format:
	ruff format app tests

compile:
	$(PYTHON) -m compileall app

test:
	pytest -v

test-integration:
	pytest -m integration -v

check: lint
	ruff format --check app tests
	$(MAKE) compile
	$(MAKE) test

build:
	$(PYTHON) -m build

run-api:
	uvicorn app.main:app --reload

clean:
	rm -rf dist build .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
