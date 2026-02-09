# LangSmith por cliente: proyecto opcional por ATSClient

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mi_app", "0015_llm_usage_log"),
    ]

    operations = [
        migrations.AddField(
            model_name="atsclient",
            name="langsmith_project",
            field=models.CharField(
                blank=True,
                help_text="Opcional. Nombre del proyecto en LangSmith para las trazas de análisis de CV de este cliente. Si está vacío se usa el proyecto por defecto.",
                max_length=100,
                verbose_name="Proyecto LangSmith",
            ),
        ),
    ]
