from django.db import migrations, models
import django.db.models.deletion


INITIAL_STATUSES = (
    ("created", "Creada"),
    ("in_review", "En revisión"),
    ("in_progress", "En progreso"),
    ("paused", "Pausada"),
    ("done", "Finalizada"),
)


def create_initial_statuses(apps, schema_editor):
    Status = apps.get_model("api", "Status")
    for tag, name in INITIAL_STATUSES:
        Status.objects.using(schema_editor.connection.alias).get_or_create(
            tag=tag,
            defaults={"name": name},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0002_request"),
    ]

    operations = [
        migrations.CreateModel(
            name="Status",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("tag", models.CharField(max_length=20, unique=True)),
                ("name", models.CharField(max_length=100)),
            ],
            options={
                "db_table": "status",
                "ordering": ["id"],
            },
        ),
        migrations.RunPython(create_initial_statuses, migrations.RunPython.noop),
        migrations.AddField(
            model_name="request",
            name="status_ref",
            field=models.ForeignKey(
                db_column="status_tag",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="requests",
                to="api.status",
                to_field="tag",
            ),
        ),
    ]
