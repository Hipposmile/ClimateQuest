# `make test` runs the whole suite (with coverage) on SQLite and then on PostgreSQL.
# PostgreSQL connection comes from PGHOST/PGPORT/PGUSER/PGPASSWORD (see ClimateQuest/settingstest.py).
PYTHON ?= python

# Third-party apps (e.g. webpush) may ship model changes without migrations; only our own apps are checked.
PROJECT_APPS = aktionen artikel community core events family forum hall_of_fame home pages personals petitions users

.PHONY: test test-sqlite test-postgres lint format migrations-check

test: migrations-check test-sqlite test-postgres

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

migrations-check:
	DJANGO_SETTINGS_MODULE=ClimateQuest.settingstest $(PYTHON) manage.py makemigrations --check --dry-run $(PROJECT_APPS)
