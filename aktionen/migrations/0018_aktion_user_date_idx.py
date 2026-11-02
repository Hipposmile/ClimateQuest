"""Add the composite index (user, date) on ``Aktion``.

What changes: one new index, no column or data is touched. Reverse: the index is dropped again.
PostgreSQL: the index is built with ``CREATE INDEX CONCURRENTLY`` so inserts/updates on the (large) table are not
blocked; the build takes roughly seconds per million rows. SQLite: plain ``CREATE INDEX``.
Verification: ``SELECT count(*) FROM aktionen_aktion`` is unchanged and
``EXPLAIN SELECT ... WHERE user_id = X AND date >= Y`` shows ``aktion_user_date_idx``.
"""

from django.db import migrations, models


class AddIndexConcurrentlyOnPostgres(migrations.AddIndex):
    """``AddIndex`` that does not block writes on PostgreSQL and behaves like ``AddIndex`` elsewhere."""

    atomic = False

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == "postgresql":
            from django.contrib.postgres.operations import AddIndexConcurrently

            AddIndexConcurrently(self.model_name, self.index).database_forwards(
                app_label, schema_editor, from_state, to_state
            )
        else:
            super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == "postgresql":
            from django.contrib.postgres.operations import RemoveIndexConcurrently

            RemoveIndexConcurrently(self.model_name, self.index.name).database_forwards(
                app_label, schema_editor, from_state, to_state
            )
        else:
            super().database_backwards(app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("aktionen", "0017_remove_category_actions_aktionenliste_category"),
    ]

    operations = [
        AddIndexConcurrentlyOnPostgres(
            model_name="aktion",
            index=models.Index(fields=["user", "date"], name="aktion_user_date_idx"),
        ),
    ]
