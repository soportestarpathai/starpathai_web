from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("mi_app", "0005_atsclient_avatar"),
    ]

    operations = [
        migrations.CreateModel(
            name="ATSFormCriterion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("label", models.CharField(max_length=200, verbose_name="Etiqueta / Criterio")),
                ("order", models.PositiveSmallIntegerField(default=0, verbose_name="Orden")),
                ("form", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="criteria", to="mi_app.atsform")),
            ],
            options={"verbose_name": "Criterio de evaluación", "verbose_name_plural": "Criterios de evaluación", "ordering": ["order", "id"]},
        ),
        migrations.CreateModel(
            name="ATSCandidateCriterionResponse",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cumple", models.BooleanField(default=False, verbose_name="Cumple")),
                ("candidate", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="criterion_responses", to="mi_app.candidate")),
                ("criterion", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="responses", to="mi_app.atsformcriterion")),
            ],
            options={"verbose_name": "Respuesta a criterio", "verbose_name_plural": "Respuestas a criterios"},
        ),
        migrations.AddConstraint(
            model_name="atscandidatecriterionresponse",
            constraint=models.UniqueConstraint(fields=("candidate", "criterion"), name="unique_candidate_criterion"),
        ),
    ]
