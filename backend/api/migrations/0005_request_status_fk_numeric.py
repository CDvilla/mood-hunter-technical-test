from django.db import migrations, models
import django.db.models.deletion


def migrate_status_fk_to_numeric(apps, schema_editor):
    Request = apps.get_model("api", "Request")
    Status = apps.get_model("api", "Status")
    database = schema_editor.connection.alias
    statuses_by_tag = dict(
        Status.objects.using(database).values_list("tag", "pk")
    )
    requests = Request.objects.using(database)
    existing_tags = set(requests.values_list("status_id", flat=True))
    unknown_tags = sorted(existing_tags - statuses_by_tag.keys())
    if unknown_tags:
        raise RuntimeError(
            "Cannot migrate request statuses to numeric IDs; catalog tags "
            f"are missing: {', '.join(unknown_tags)}."
        )

    for tag, status_pk in statuses_by_tag.items():
        requests.filter(status_id=tag).update(status_numeric_id=status_pk)

    unmigrated_count = requests.filter(status_numeric__isnull=True).count()
    mismatched_count = sum(
        1
        for legacy_tag, numeric_id in requests.values_list(
            "status_id",
            "status_numeric_id",
        )
        if statuses_by_tag[legacy_tag] != numeric_id
    )
    if unmigrated_count or mismatched_count:
        raise RuntimeError(
            "Request status conversion to numeric IDs failed: "
            f"{unmigrated_count} requests are unmigrated and "
            f"{mismatched_count} have mismatched statuses."
        )


def restore_status_fk_to_tag(apps, schema_editor):
    Request = apps.get_model("api", "Request")
    Status = apps.get_model("api", "Status")
    database = schema_editor.connection.alias
    tags_by_pk = dict(
        Status.objects.using(database).values_list("pk", "tag")
    )
    requests = Request.objects.using(database)
    for status_pk, tag in tags_by_pk.items():
        requests.filter(status_numeric_id=status_pk).update(status=tag)

    mismatched_count = sum(
        1
        for tag, numeric_id in requests.values_list("status", "status_numeric_id")
        if tags_by_pk[numeric_id] != tag
    )
    if mismatched_count:
        raise RuntimeError(
            "Could not restore the request status tags for "
            f"{mismatched_count} requests."
        )


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0004_migrate_request_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="request",
            name="status_numeric",
            field=models.ForeignKey(
                db_column="status_id",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="api.status",
            ),
        ),
        migrations.RunPython(
            migrate_status_fk_to_numeric,
            restore_status_fk_to_tag,
        ),
        migrations.RemoveField(
            model_name="request",
            name="status",
        ),
        migrations.RenameField(
            model_name="request",
            old_name="status_numeric",
            new_name="status",
        ),
        migrations.AlterField(
            model_name="request",
            name="status",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="requests",
                to="api.status",
            ),
        ),
    ]
