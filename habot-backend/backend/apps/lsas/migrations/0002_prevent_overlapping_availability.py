from django.db import migrations


CREATE_OVERLAP_GUARD = """
CREATE OR REPLACE FUNCTION prevent_overlapping_availability()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM lsas_availability existing
        WHERE existing.lsa_id = NEW.lsa_id
          AND existing.date = NEW.date
          AND existing.id <> NEW.id
          AND NEW.start_time < existing.end_time
          AND NEW.end_time > existing.start_time
    ) THEN
        RAISE EXCEPTION 'Availability slots for an LSA cannot overlap';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER availability_prevent_overlap
BEFORE INSERT OR UPDATE OF lsa_id, date, start_time, end_time
ON lsas_availability
FOR EACH ROW EXECUTE FUNCTION prevent_overlapping_availability();
"""

DROP_OVERLAP_GUARD = """
DROP TRIGGER IF EXISTS availability_prevent_overlap ON lsas_availability;
DROP FUNCTION IF EXISTS prevent_overlapping_availability();
"""


def create_overlap_guard(apps, schema_editor):
    # PostgreSQL is the production database. SQLite remains intentionally usable
    # for the fast, isolated test suite.
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(CREATE_OVERLAP_GUARD)


def drop_overlap_guard(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(DROP_OVERLAP_GUARD)


class Migration(migrations.Migration):
    dependencies = [("lsas", "0001_initial")]

    operations = [migrations.RunPython(create_overlap_guard, drop_overlap_guard)]
