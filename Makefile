VERSION := 0.1.0
PACKAGE := rlc-cloud-repos
PY_PACKAGE := rlc_cloud_repos

.PHONY: install clean test lint sdist rpm

install:
	@echo "🔧 Installing $(PACKAGE) globally..."
	pip install --root=/ --prefix=/usr -e .

dist: 
	python3 -m build

sdist: dist
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
	rm -rf rpm/[0-9]*.patch
	find ./ -type d -name "*.egg-info" -exec rm -rf {} +
	find ./ -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.dist-info" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf ~/.cache/pip/wheels/*

rpm: dist
	@echo "📆 Repackaging tarball with dash-name for RPM..."
	rm -rf build/tmp && mkdir -p build/tmp
	tar -xzf dist/$(PY_PACKAGE)-$(VERSION).tar.gz -C build/tmp
	mv build/tmp/$(PY_PACKAGE)-$(VERSION) build/tmp/$(PACKAGE)-$(VERSION)
	tar -czf dist/$(PACKAGE)-$(VERSION).tar.gz -C build/tmp $(PACKAGE)-$(VERSION)

	@echo "📄 Copying tarball into SOURCES for rpmbuild..."
	mkdir -p ~/rpmbuild/SOURCES
	cp dist/$(PACKAGE)-$(VERSION).tar.gz ~/rpmbuild/SOURCES/

	@echo "🚰 Running rpmbuild..."
	if ! rpmbuild -ba rpm/$(PACKAGE).spec; then \
		echo "💥 RPM build failed. Ensure BuildRequires includes pyproject macros or fallback to pip install."; \
		exit 1; \
	fi

mock: dist
	@echo "📦 Building SRPM..."
	# Repackage with dash-name expected by RPM
	rm -rf build/tmp && mkdir -p build/tmp
	tar -xzf dist/rlc_cloud_repos-*.tar.gz -C build/tmp
	mv build/tmp/rlc_cloud_repos-* build/tmp/rlc-cloud-repos-$(VERSION)
	tar -czf rpm/rlc-cloud-repos-$(VERSION).tar.gz -C build/tmp rlc-cloud-repos-$(VERSION)
	# Run packit
	packit srpm --output dist/
	@echo "🧪 Running mock build..."
	mock -r rocky-9-x86_64 --resultdir=dist --enable-network dist/*.src.rpm

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

