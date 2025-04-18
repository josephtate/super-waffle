VERSION := $(shell python3 -c "from rlc_cloud_repos import __version__; print(__version__)" 2>/dev/null)
PACKAGE := rlc-cloud-repos
PY_PACKAGE := rlc_cloud_repos
distdir := dist

.PHONY: install clean test lint sdist rpm spec dev mock

$(distdir)/rpm/$(PACKAGE).spec:
	@echo "📄 Generating RPM spec file..."
	mkdir -p $(distdir)/rpm
	sed -e 's/^\(Version:\s*\)VERSION/\1$(VERSION)/' rpm/$(PACKAGE).spec.in > $(distdir)/rpm/$(PACKAGE).spec

spec: $(distdir)/rpm/$(PACKAGE).spec

dev:
	@echo "🔧 Installing development dependencies..."
	pip install -e .[dev]

install:
	@echo "🔧 Installing $(PACKAGE) globally..."
	pip install --root=/ --prefix=/usr -e .

dist:
	@echo "🛞 Building wheel..."
	python3 -m build --wheel

$(distdir)/$(PY_PACKAGE)-$(VERSION).tar.gz: setup.cfg setup.py $(shell find src -name '*.py')
	@echo "📦 Building source distribution..."
	python3 -m build --sdist

sdist: $(distdir)/$(PY_PACKAGE)-$(VERSION).tar.gz

lint:
	@echo "🔍 Running linters..."
	black --check src tests
	isort --check-only src tests
	flake8 src tests

clean:
	@echo "🦚 Cleaning build artifacts..."
	rm -f rpm/$(PACKAGE).spec rpm/*.tar.gz
	rm -rf build dist
	rm -rf rpm/[0-9]*.patch
	find ./ -type d -name "*.egg-info" -exec rm -rf {} +
	find ./ -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.dist-info" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf ~/.cache/pip/wheels/*
	rm -f .coverage

rpm-tarball: spec sdist
	# RPM expects a dash name, but python's sdist replaces - with _
	@echo "📆 Repackaging tarball with dash-name for RPM..."
	rm -rf build/tmp && mkdir -p build/tmp
	tar -xzf dist/$(PY_PACKAGE)-$(VERSION).tar.gz -C build/tmp
	mv build/tmp/$(PY_PACKAGE)-$(VERSION) build/tmp/$(PACKAGE)-$(VERSION)
	tar -czf dist/$(PACKAGE)-$(VERSION).tar.gz -C build/tmp $(PACKAGE)-$(VERSION)

rpm: rpm-tarball
	@echo "📄 Copying tarball into SOURCES for rpmbuild..."
	mkdir -p ~/rpmbuild/SOURCES
	cp dist/$(PACKAGE)-$(VERSION).tar.gz ~/rpmbuild/SOURCES/

	@echo "🚰 Running rpmbuild..."
	if ! rpmbuild -ba rpm/$(PACKAGE).spec; then \
		echo "💥 RPM build failed. Ensure BuildRequires includes pyproject macros or fallback to pip install."; \
		exit 1; \
	fi

mock: spec rpm-tarball
	@echo "📦 Building SRPM..."
	# Run packit
	packit --debug srpm --output dist/
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

