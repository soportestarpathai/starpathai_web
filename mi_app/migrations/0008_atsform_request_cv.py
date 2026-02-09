from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mi_app", "0007_remove_atscandidatecriterionresponse_unique_candidate_criterion_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="atsform",
            name="request_cv",
            field=models.BooleanField(
                default=False,
                help_text="Si está activo, el formulario público incluirá un campo para subir CV (PDF/DOC).",
                verbose_name="Solicitar CV",
            ),
        ),
    ]
