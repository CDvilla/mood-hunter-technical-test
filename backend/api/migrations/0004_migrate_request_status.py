from django.db import migrations, models
import django.db.models.deletion
from django.db.models import F


INITIAL_STATUS_TAGS = {
    "created",
    "in_review",
    "in_progress",
    "paused",
    "done",
}


def migrate_request_statuses(apps, schema_editor):
    Request = apps.get_model("api", "Request")
    Status = apps.get_model("api", "Status")
    database = schema_editor.connection.alias
    existing_tags = set(
        Status.objects.using(database)
        .filter(tag__in=INITIAL_STATUS_TAGS)
        .values_list("tag", flat=True)
    )
    if existing_tags != INITIAL_STATUS_TAGS:
        missing_tags = sorted(INITIAL_STATUS_TAGS - existing_tags)
        raise RuntimeError(
            "Cannot migrate requests: initial statuses are missing: "
            f"{', '.join(missing_tags)}."
        )

    requests = Request.objects.using(database)
    legacy_tags = set(requests.values_list("status", flat=True).distinct())
    unknown_tags = sorted(legacy_tags - INITIAL_STATUS_TAGS)
    if unknown_tags:
        raise RuntimeError(
            "Cannot migrate requests with unknown legacy statuses: "
            f"{', '.join(unknown_tags)}. Resolve these values before retrying."
        )

    for tag in INITIAL_STATUS_TAGS:
        requests.filter(status=tag).update(status_ref_id=tag)

    unmigrated_count = requests.filter(status_ref__isnull=True).count()
    mismatched_count = requests.exclude(status_ref_id=F("status")).count()
    if unmigrated_count or mismatched_count:
        raise RuntimeError(
            "Request status migration did not complete successfully: "
            f"{unmigrated_count} requests are unmigrated and "
            f"{mismatched_count} have mismatched status tags."
        )


def restore_request_statuses(apps, schema_editor):
    Request = apps.get_model("api", "Request")
    requests = Request.objects.using(schema_editor.connection.alias)
    requests.update(status=F("status_ref_id"))
    mismatched_count = requests.exclude(status=F("status_ref_id")).count()
    if mismatched_count:
        raise RuntimeError(
            "Could not restore legacy request statuses for "
            f"{mismatched_count} requests."
        )


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0003_status_catalog_and_request_fk"),
    ]

    operations = [
        migrations.RunPython(migrate_request_statuses, restore_request_statuses),
        migrations.RemoveField(
            model_name="request",
            name="status",
        ),
        migrations.RenameField(
            model_name="request",
            old_name="status_ref",
            new_name="status",
        ),
        migrations.AlterField(
            model_name="request",
            name="status",
            field=models.ForeignKey(
                db_column="status_tag",
                default="created",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="requests",
                to="api.status",
                to_field="tag",
            ),
        ),
    ]
