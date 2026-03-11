.PHONY: sync test build install clean

UV ?= uv
PYTHON_VERSION ?= 3.13
APP_NAME := gradescope_fake_assignment
ENTRYPOINT := src/gradescope_fake_assignment/__main__.py
TEST_ROSTER := tests/resources/test-roster.csv
BAD_ROSTER := tests/resources/test-roster-bad-columns.csv

sync:
	$(UV) sync --python $(PYTHON_VERSION)

# Smoke-check the CLI with good and bad roster inputs.
test: sync
	@tmp_dir=$$(mktemp -d); \
		echo "Running smoke checks in $$tmp_dir"; \
		$(UV) run --python $(PYTHON_VERSION) python -m $(APP_NAME) "Assignment 1" "$(TEST_ROSTER)" --format standard --output_dir "$$tmp_dir"; \
		test -f "$$tmp_dir/template.pdf"; \
		test -f "$$tmp_dir/submissions.pdf"; \
		bad_out=$$($(UV) run --python $(PYTHON_VERSION) python -m $(APP_NAME) "Assignment 1" "$(BAD_ROSTER)" --format standard --output_dir "$$tmp_dir" 2>&1 || true); \
		echo "$$bad_out" | grep -q "missing the required column"; \
		rm -rf "$$tmp_dir"

build: sync
	$(UV) run --python $(PYTHON_VERSION) pyinstaller --onefile $(ENTRYPOINT) --name $(APP_NAME)

install: build
	sudo mv ./dist/$(APP_NAME) /usr/local/bin/

clean:
	rm -rf build dist *.spec output .pytest_cache .mypy_cache
	find src tests -type d -name '__pycache__' -prune -exec rm -rf {} +
