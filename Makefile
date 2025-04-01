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

rpm: sdist
	@echo "📆 Repackaging tarball with dash-name for RPM..."
	rm -rf build/tmp && mkdir -p build/tmp
	tar -xzf dist/$(PY_PACKAGE)-$(VERSION).tar.gz -C build/tmp
	mv build/tmp/$(PY_PACKAGE)-$(VERSION) build/tmp/$(PACKAGE)-$(VERSION)
	tar -czf dist/$(PACKAGE)-$(VERSION).tar.gz -C build/tmp $(PACKAGE)-$(VERSION)

	@echo "📄 Copying tarball into SOURCES for rpmbuild..."
	mkdir -p ~/rpmbuild/SOURCES
	cp dist/$(PACKAGE)-$(VERSION).tar.gz ~/rpmbuild/SOURCES/

	@echo "🚰 Running rpmbuild..."
	if ! rpmbuild -ba $(PACKAGE).spec; then \
		echo "💥 RPM build failed. Ensure BuildRequires includes pyproject macros or fallback to pip install."; \
		exit 1; \
	fi

test:
	@echo "🤪 Running tests..."
	PYTHONPATH=src python3 tests/test_cloud_repos.py

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

RPM_FILE := $(shell find ~/rpmbuild/RPMS/noarch -name 'rlc-cloud-repos-*.rpm' | sort -V | tail -n 1)
REMOTE_USER := rocky
REMOTE_HOST := 54.88.46.215
REMOTE_PATH := /home/rocky/

publish: 
	@echo "📦 Publishing latest RPM to $(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_PATH)"
	scp /home/jhanger/rpmbuild/RPMS/noarch/rlc-cloud-repos-0.1.0-1.el9.noarch.rpm ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}
	ssh $(REMOTE_USER)@$(REMOTE_HOST) 'sudo rpm -e rlc-cloud-repos || true'
	ssh $(REMOTE_USER)@$(REMOTE_HOST) 'sudo rpm -Uvh --nodeps $(notdir $(RPM_FILE)) && rlc-cloud-repos'

test-remote:
	ssh $(REMOTE_USER)@$(REMOTE_HOST) 'rlc-cloud-repos'