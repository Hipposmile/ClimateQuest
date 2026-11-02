"""Migrations apply and reverse cleanly on the configured database (SQLite and PostgreSQL)."""

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

BEFORE = [("aktionen", "0017_remove_category_actions_aktionenliste_category")]
AFTER = [("aktionen", "0018_aktion_user_date_idx")]
INDEX = "aktion_user_date_idx"


def index_names():
    with connection.cursor() as cursor:
        return set(connection.introspection.get_constraints(cursor, "aktionen_aktion"))


@pytest.mark.django_db(transaction=True)
def test_user_date_index_migration_is_reversible_and_keeps_data():
    executor = MigrationExecutor(connection)
    executor.migrate(AFTER)
    from django.apps import apps

    user_model = apps.get_model("auth", "User")
    user = user_model.objects.create_user("migrator")
    action_list = apps.get_model("aktionen", "AktionenListe").objects.create(
        name="m",
        name_en="m",
        klimapunkte=1,
        mengeBeschreibung="x",
        mengeBeschreibung_en="x",
        mengeBeschreibungSingular="x",
        mengeBeschreibungSingular_en="x",
        anmerkung="",
        anmerkung_en="",
        source="",
        source_en="",
    )
    apps.get_model("aktionen", "Aktion").objects.create(user=user, aktion=action_list, quantity=2)
    assert INDEX in index_names()

    executor = MigrationExecutor(connection)
    executor.migrate(BEFORE)
    assert INDEX not in index_names()
    assert apps.get_model("aktionen", "Aktion").objects.count() == 1  # rows survive the rollback

    executor = MigrationExecutor(connection)
    executor.migrate(AFTER)
    assert INDEX in index_names()
    assert apps.get_model("aktionen", "Aktion").objects.get().quantity == 2
