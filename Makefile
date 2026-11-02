# `make test` runs the whole suite (with coverage) on SQLite and then on PostgreSQL.
# PostgreSQL connection comes from PGHOST/PGPORT/PGUSER/PGPASSWORD (see ClimateQuest/settingstest.py).
PYTHON ?= python

.PHONY: test test-sqlite test-postgres lint format

test: test-sqlite test-postgres

test-sqlite:
	TEST_DB=sqlite $(PYTHON) -m coverage run -m pytest -q
	$(PYTHON) -m coverage report --fail-under=100

test-postgres:
	TEST_DB=postgres $(PYTHON) -m coverage run -m pytest -q
	$(PYTHON) -m coverage report --fail-under=100

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

format:
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m ruff format .
