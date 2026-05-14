import uuid

from django.db import migrations, models


def populate_vacancy_public_ids(apps, schema_editor):
    Vacancy = apps.get_model("mi_app", "Vacancy")
    for vacancy in Vacancy.objects.filter(public_id__isnull=True).only("id", "public_id"):
        vacancy.public_id = uuid.uuid4()
        vacancy.save(update_fields=["public_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("mi_app", "0027_candidate_public_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="vacancy",
            name="public_id",
            field=models.UUIDField(blank=True, null=True, editable=False, verbose_name="ID público"),
        ),
        migrations.RunPython(populate_vacancy_public_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="vacancy",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name="ID público"),
        ),
    ]
