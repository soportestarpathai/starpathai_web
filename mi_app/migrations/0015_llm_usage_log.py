# Generated for LangSmith / consumo IA: registro de tokens por análisis de CV

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("mi_app", "0014_cv_analysis_config_and_vacancy_profile"),
    ]

    operations = [
        migrations.CreateModel(
            name="LLMUsageLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("prompt_tokens", models.PositiveIntegerField(default=0, verbose_name="Tokens entrada")),
                ("completion_tokens", models.PositiveIntegerField(default=0, verbose_name="Tokens salida")),
                ("total_tokens", models.PositiveIntegerField(default=0, verbose_name="Total tokens")),
                ("model", models.CharField(blank=True, max_length=64, verbose_name="Modelo")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "candidate",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="llm_usage_logs",
                        to="mi_app.candidate",
                    ),
                ),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="llm_usage_logs",
                        to="mi_app.atsclient",
                    ),
                ),
            ],
            options={
                "verbose_name": "Uso IA (tokens)",
                "verbose_name_plural": "Uso IA (tokens)",
                "ordering": ["-created_at"],
            },
        ),
    ]
