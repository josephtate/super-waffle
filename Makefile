VERSION := $(shell python -m 'rlc.cloud_repos' 2>/dev/null)
$(info "VERSION: $(VERSION)")
GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

PACKAGE := rlc.cloud-repos
PY_PACKAGE := rlc.cloud_repos
RPM_PACKAGE := python3-rlc-cloud-repos
distdir := dist

.PHONY: install clean test lint dist rpm spec dev mock

$(distdir)/$(RPM_PACKAGE).spec: rpm/$(RPM_PACKAGE).spec.in
	@echo "📄 Generating RPM spec file..."
	@echo "  Version: $(VERSION)"
	mkdir -p $(distdir)
	sed -e 's/^\(Version:\s*\)VERSION/\1'$(VERSION)'/' rpm/$(RPM_PACKAGE).spec.in > $(distdir)/$(RPM_PACKAGE).spec

spec: $(distdir)/$(RPM_PACKAGE).spec

dev:
	@echo "🔧 Installing development dependencies..."
	pip install $(PIP_OPTIONS) -e .[dev]
	pip install $(PIP_OPTIONS) -e ./framework[dev]

install:
	@echo "🔧 Installing $(PACKAGE) globally..."
	pip install --root=/ --prefix=/usr -e .

$(distdir)/$(PY_PACKAGE)-$(VERSION)-py3-none-any.whl: setup.cfg setup.py MANIFEST.in $(shell find cloud-repos -name '*.py') config/* data/*
	@echo "🛞 Building wheel..."
	python3 -m build --wheel

dist: $(distdir)/$(PY_PACKAGE)-$(VERSION)-py3-none-any.whl

$(distdir)/$(PACKAGE)-$(VERSION).tar.gz: setup.cfg setup.py MANIFEST.in $(shell find cloud-repos -name '*.py') config/* data/*
	@echo "📦 Building source distribution..."
	python3 -m build --sdist

sdist: $(distdir)/$(PACKAGE)-$(VERSION).tar.gz

lint:
	@echo "🔍 Running linters..."
	black --check cloud-repos framework tests
	isort --check-only cloud-repos framework tests
	flake8 cloud-repos framework tests

clean:
	@echo "🦚 Cleaning build artifacts..."
	# rm -f rpm/$(RPM_PACKAGE).spec rpm/*.tar.gz
	rm -rf build dist framework/build framework/dist
	rm -rf rpm/[0-9]*.patch
	find ./ -type d -name "*.egg-info" -exec rm -rf {} +
	find ./ -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.dist-info" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.orig" -exec rm -f {} +
	find . -type f -name "*.rej" -exec rm -f {} +
	rm -rf ~/.cache/pip/wheels/*
	rm -f .coverage

rpm: spec sdist
	@echo "📄 Copying tarball into SOURCES for rpmbuild..."
	mkdir -p ~/rpmbuild/SOURCES
	cp dist/$(PACKAGE)-$(VERSION).tar.gz ~/rpmbuild/SOURCES/

	@echo "🚰 Running rpmbuild..."
	if ! rpmbuild -ba $(distdir)/$(RPM_PACKAGE).spec; then \
		echo "💥 RPM build failed. Ensure BuildRequires includes pyproject macros or fallback to pip install."; \
		exit 1; \
	fi

mock: spec sdist
	@echo "📦 Building SRPM..."
	mkdir -p $(distdir)/rpm
	cp dist/$(RPM_PACKAGE).spec $(distdir)/rpm/
	cp dist/$(PACKAGE)-$(VERSION).tar.gz $(distdir)/rpm/
	# Run packit with current branch
	packit --debug srpm --output dist/ --upstream-ref $(GIT_BRANCH)
	@echo "🧪 Running mock build..."
	mock -r rocky-9-x86_64 --resultdir=dist --enable-network dist/*.src.rpm

# Testing
PYTHON ?= python3
PYTHONPATH := src
PYTHON_VERSION ?= 3.11

.PHONY: test test-coverage test-podman

test-podman:
	@echo "🐋 Running tests in Podman container with Python $(PYTHON_VERSION)..."
	podman pull docker.io/library/python:$(PYTHON_VERSION)
	podman run --rm -v .:/app:Z -w /app python:$(PYTHON_VERSION) bash -c \
		"python -m pip install --upgrade pip setuptools && make dev && python -m pytest --cov --cov-report=term-missing"

test:
	@echo "🧪 Running test suite with pytest..."
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -v tests --cov --cov-report=term-missing

test-coverage:
	pytest --cov --cov-report=term-missing

all: clean rpm publish clean

# Include local overrides
-include Makefile.local

