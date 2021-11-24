from django.db import migrations
from django.db.migrations.operations import RunSQL


class Migration(migrations.Migration):

    dependencies = [
        ("bibleverses", "0002_auto_20161209_1825"),
    ]

    operations = [
        RunSQL(
            "DROP INDEX IF EXISTS bibleverses_verse_tsv_index;"
            "CREATE INDEX bibleverses_verse_tsv_index ON bibleverses_verse USING gin(text_tsv);"
            "UPDATE bibleverses_verse SET text_tsv = to_tsvector(text_saved);",
            reverse_sql="",
        )
    ]
