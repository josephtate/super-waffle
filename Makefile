VERSION := 0.1.0
PACKAGE := rlc-cloud-repos
PY_PACKAGE := rlc_cloud_repos

.PHONY: install clean test lint sdist rpm

install:
	@echo "🔧 Installing $(PACKAGE) globally..."
	pip install --root=/ --prefix=/usr -e .

sdist:
	@echo "📆 Building source distribution tarball..."
	python3 -m build --sdist

lint:
	@echo "🔍 Running linters..."
	black --check src tests
	isort --check-only src tests
	flake8 src tests

clean:
	@echo "🦚 Cleaning build artifacts..."
	rm -rf build dist
	find ./ -type d -name "*.egg-info" -exec rm -rf {} +
	find ./ -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.dist-info" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf ~/.cache/pip/wheels/*

# Testing
PYTHON ?= python3
PYTHONPATH := src

.PHONY: test
test:
	@echo "🧪 Running test suite with pytest..."
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -v tests

test-coverage:
	pytest --cov=src/rlc_cloud_repos --cov-report=term-missing

all: clean rpm publish clean

# Include local overrides
-include Makefile.local

