PYTHON ?= python3
SRC := quotai.py
TESTS := tests

.PHONY: fmt fmt-check lint test smoke build clean

fmt:
	$(PYTHON) -m black $(SRC) $(TESTS)

fmt-check:
	$(PYTHON) -m black --check $(SRC) $(TESTS)

lint:
	$(PYTHON) -m ruff check $(SRC) $(TESTS)
	$(PYTHON) -m pylint $(SRC)

test:
	$(PYTHON) -m unittest discover -s $(TESTS)
	$(PYTHON) -m py_compile $(SRC)

smoke:
	$(PYTHON) $(SRC) --version
	$(PYTHON) $(SRC) --help >/dev/null

build:
	$(PYTHON) -m build

clean:
	rm -rf build dist *.egg-info
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache -o -name .mypy_cache \) -prune -exec rm -rf {} +
