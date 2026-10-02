PYTHON ?= .venv/bin/python
SYSTEM_PYTHON ?= python3
DIST_DIR ?= dist
UVX ?= .venv/bin/uvx

.PHONY: help setup test test-parity fixtures-vibes lint typecheck check sdist uvx-test package clean

help:
	@printf '%s\n' \
		'setup      Create .venv and install development dependencies' \
		'test       Run the complete pytest suite' \
		'test-parity Run the Tau-owned canonical parity suite' \
		'fixtures-vibes Run the shared fixtures-vibes compliance suite' \
		'lint       Run Ruff checks' \
		'typecheck  Run MyPy checks' \
		'check      Run tests, lint, and type checking' \
		'sdist      Build the canonical source distribution' \
		'uvx-test   Install the sdist with uvx and run a CLI smoke test' \
		'package    Test with pytest and uvx, then build a commit-stamped archive' \
		'clean      Remove generated package artifacts'

setup:
	$(SYSTEM_PYTHON) -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements-dev.txt

test:
	PATH="$(dir $(PYTHON)):$$PATH" PYTHONPATH=src $(PYTHON) -m pytest -q

test-parity:
	@mkdir -p tests/parity/node_modules
	@ln -sfn ../../../src/tau_web/vibes/node_modules/pngjs tests/parity/node_modules/pngjs
	@ln -sfn ../../../src/tau_web/vibes/node_modules/pixelmatch tests/parity/node_modules/pixelmatch
	@ln -sfn ../../../src/tau_web/vibes/node_modules/playwright tests/parity/node_modules/playwright
	@trap 'rm -rf tests/parity/node_modules' EXIT; bun test tests/parity

fixtures-vibes:
	$(MAKE) -C references/fixtures-vibes deps compliance PROFILE=$(CURDIR)/tests/fixtures-vibes/profile.json

lint:
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy

check: test lint typecheck

sdist:
	@mkdir -p $(DIST_DIR)
	@$(PYTHON) -c 'import build_backend; print(build_backend.build_sdist("$(DIST_DIR)"))'

uvx-test: sdist
	@version=`$(PYTHON) -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])'`; \
	$(UVX) --refresh --from "$(DIST_DIR)/tau_prime-$$version.tar.gz" tau --help >/dev/null

package: test uvx-test
	@version=`$(PYTHON) -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])'`; \
	commit=`git rev-parse --short HEAD`; \
	source="$(DIST_DIR)/tau_prime-$$version.tar.gz"; \
	target="$(DIST_DIR)/tau-prime-$$commit-$$version.tar.gz"; \
	cp "$$source" "$$target"; \
	tar -tzf "$$target" >/dev/null; \
	if command -v sha256sum >/dev/null 2>&1; then sha256sum "$$target"; \
	else shasum -a 256 "$$target"; fi

clean:
	rm -f $(DIST_DIR)/tau_prime-*.tar.gz $(DIST_DIR)/tau-prime-*.tar.gz
