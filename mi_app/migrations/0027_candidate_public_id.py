import uuid

from django.db import migrations, models


def populate_candidate_public_ids(apps, schema_editor):
    Candidate = apps.get_model("mi_app", "Candidate")
    for candidate in Candidate.objects.filter(public_id__isnull=True).only("id", "public_id"):
        candidate.public_id = uuid.uuid4()
        candidate.save(update_fields=["public_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("mi_app", "0026_subscription_module_account_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="candidate",
            name="public_id",
            field=models.UUIDField(blank=True, null=True, editable=False, verbose_name="ID público"),
        ),
        migrations.RunPython(populate_candidate_public_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="candidate",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name="ID público"),
        ),
    ]
