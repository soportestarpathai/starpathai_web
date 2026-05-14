import uuid

from django.db import migrations, models


def populate_workforce_public_ids(apps, schema_editor):
    WorkforceArea = apps.get_model("mi_app", "WorkforceArea")
    WorkforcePosition = apps.get_model("mi_app", "WorkforcePosition")
    for area in WorkforceArea.objects.filter(public_id__isnull=True).only("id", "public_id"):
        area.public_id = uuid.uuid4()
        area.save(update_fields=["public_id"])
    for position in WorkforcePosition.objects.filter(public_id__isnull=True).only("id", "public_id"):
        position.public_id = uuid.uuid4()
        position.save(update_fields=["public_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("mi_app", "0029_workforce_module"),
    ]

    operations = [
        migrations.AddField(
            model_name="workforcearea",
            name="public_id",
            field=models.UUIDField(blank=True, null=True, editable=False, verbose_name="ID público"),
        ),
        migrations.AddField(
            model_name="workforceposition",
            name="public_id",
            field=models.UUIDField(blank=True, null=True, editable=False, verbose_name="ID público"),
        ),
        migrations.RunPython(populate_workforce_public_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="workforcearea",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name="ID público"),
        ),
        migrations.AlterField(
            model_name="workforceposition",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name="ID público"),
        ),
    ]
