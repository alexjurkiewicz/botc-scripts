from django.db import migrations

BACKFILL = """
    INSERT INTO scripts_scriptversioncharacter (script_version_id, character_id)
    SELECT DISTINCT
        sv.id,
        CASE WHEN jsonb_typeof(entry) = 'string' THEN entry #>> '{}' ELSE entry ->> 'id' END AS character_id
    FROM scripts_scriptversion sv, jsonb_array_elements(sv.content) AS entry
    WHERE jsonb_typeof(sv.content) = 'array'
      AND CASE WHEN jsonb_typeof(entry) = 'string' THEN entry #>> '{}' ELSE entry ->> 'id' END
          NOT IN ('', '_meta')
    ON CONFLICT DO NOTHING;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("scripts", "0047_scriptversioncharacter"),
    ]

    operations = [
        migrations.RunSQL(BACKFILL, migrations.RunSQL.noop),
    ]
