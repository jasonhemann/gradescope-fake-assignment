.PHONY: sync format lint lint-fix typecheck test coverage check build install clean

UV ?= uv
PYTHON_VERSION ?= 3.13
APP_NAME := gradescope_fake_assignment
ENTRYPOINT := src/gradescope_fake_assignment/__main__.py
INSTALL_DIR ?= $(HOME)/.local/bin
CANVAS_ROSTER := tests/resources/test-roster.csv
BANNER_ROSTER := tests/resources/test-roster-banner.csv
BAD_ROSTER := tests/resources/test-roster-bad-columns.csv

sync:
	$(UV) sync --python $(PYTHON_VERSION)

format: sync
	$(UV) run --python $(PYTHON_VERSION) ruff format src tests

lint: sync
	$(UV) run --python $(PYTHON_VERSION) ruff check src tests

lint-fix: sync
	$(UV) run --python $(PYTHON_VERSION) ruff check src tests --fix

typecheck: sync
	$(UV) run --python $(PYTHON_VERSION) basedpyright

# Smoke-check the CLI with good and bad roster inputs.
test: sync
	$(UV) run --python $(PYTHON_VERSION) pytest -q
	@set -eu; \
			tmp_dir=$$(mktemp -d); \
			trap 'rm -rf "$$tmp_dir"' EXIT; \
			echo "Running smoke checks in $$tmp_dir"; \
			canvas_dir=$$tmp_dir/canvas; \
			banner_dir=$$tmp_dir/banner; \
			mkdir -p "$$canvas_dir" "$$banner_dir"; \
			$(UV) run --python $(PYTHON_VERSION) python -m $(APP_NAME) "Assignment 1" "$(CANVAS_ROSTER)" --format canvas --output_dir "$$canvas_dir"; \
			test -f "$$canvas_dir/template.pdf"; \
			test -f "$$canvas_dir/submissions.pdf"; \
			$(UV) run --python $(PYTHON_VERSION) python -m $(APP_NAME) "Assignment 1" "$(BANNER_ROSTER)" --format banner --output_dir "$$banner_dir"; \
			test -f "$$banner_dir/template.pdf"; \
			test -f "$$banner_dir/submissions.pdf"; \
			if bad_out=$$($(UV) run --python $(PYTHON_VERSION) python -m $(APP_NAME) "Assignment 1" "$(BAD_ROSTER)" --format canvas --output_dir "$$tmp_dir/bad" 2>&1); then \
				echo "Malformed roster unexpectedly succeeded" >&2; \
				exit 1; \
			fi; \
			printf '%s\n' "$$bad_out" | grep -q "missing the required column"; \
			test ! -e "$$tmp_dir/bad"

coverage:
	@echo "Coverage target (warn-only in wave 1): 80%"
	@$(MAKE) test

check: lint typecheck test

build: sync
	$(UV) run --python $(PYTHON_VERSION) pyinstaller --clean --onefile $(ENTRYPOINT) --name $(APP_NAME)

install: build
	mkdir -p "$(INSTALL_DIR)"
	install -m 755 ./dist/$(APP_NAME) "$(INSTALL_DIR)/$(APP_NAME)"

clean:
	rm -rf build dist *.spec output .pytest_cache .mypy_cache .ruff_cache
	find src tests -type d -name '__pycache__' -prune -exec rm -rf {} +
