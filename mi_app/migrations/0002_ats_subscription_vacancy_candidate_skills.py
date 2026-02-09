# Generated for ATS SaaS: Subscription, Vacancy, Candidate, SkillEvaluation

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("mi_app", "0001_ats_client"),
    ]

    operations = [
        migrations.CreateModel(
            name="Subscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("plan", models.CharField(choices=[("FREE", "Gratuito"), ("PRO", "Pro"), ("ENTERPRISE", "Enterprise")], default="FREE", max_length=50, verbose_name="Plan")),
                ("cvs_used", models.PositiveIntegerField(default=0, verbose_name="CVs usados")),
                ("cvs_limit", models.PositiveIntegerField(default=10, verbose_name="Límite de CVs")),
                ("next_payment_date", models.DateField(blank=True, null=True, verbose_name="Próximo pago")),
                ("amount", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="Monto (MXN)")),
                ("active", models.BooleanField(default=True, verbose_name="Activa")),
                ("paypal_subscription_id", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ats_subscription",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Suscripción ATS",
                "verbose_name_plural": "Suscripciones ATS",
            },
        ),
        migrations.CreateModel(
            name="Vacancy",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255, verbose_name="Título")),
                ("description", models.TextField(blank=True, verbose_name="Descripción")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="vacancies",
                        to="mi_app.atsclient",
                    ),
                ),
            ],
            options={
                "verbose_name": "Vacante",
                "verbose_name_plural": "Vacantes",
            },
        ),
        migrations.CreateModel(
            name="Candidate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, verbose_name="Nombre")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="Email")),
                ("score", models.FloatField(default=0, verbose_name="Score general (0-100)")),
                (
                    "status",
                    models.CharField(
                        choices=[("APTO", "Apto"), ("REVISION", "En revisión"), ("NO_APTO", "No apto")],
                        default="REVISION",
                        max_length=20,
                        verbose_name="Estado",
                    ),
                ),
                ("match_percentage", models.FloatField(blank=True, null=True, verbose_name="Coincidencia con vacante (%)")),
                ("analysis_date", models.DateTimeField(auto_now_add=True, verbose_name="Fecha de análisis")),
                ("explanation_text", models.TextField(blank=True, help_text="Por qué es apto / no apto en lenguaje humano.", verbose_name="Explicación (generada por LLM)")),
                ("cv_file", models.FileField(blank=True, null=True, upload_to="ats/cvs/%Y/%m/", verbose_name="Archivo CV")),
                ("raw_text", models.TextField(blank=True, verbose_name="Texto extraído del CV (OCR)")),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="candidates",
                        to="mi_app.atsclient",
                    ),
                ),
                (
                    "vacancy",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="candidates",
                        to="mi_app.vacancy",
                    ),
                ),
            ],
            options={
                "verbose_name": "Candidato",
                "verbose_name_plural": "Candidatos",
                "ordering": ["-analysis_date"],
            },
        ),
        migrations.CreateModel(
            name="SkillEvaluation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("skill", models.CharField(max_length=100, verbose_name="Habilidad")),
                ("level", models.PositiveSmallIntegerField(default=0, help_text="0-100, generado por LLM.", verbose_name="Nivel (0-100)")),
                ("match_percentage", models.FloatField(blank=True, null=True, verbose_name="Coincidencia con vacante (%)")),
                (
                    "candidate",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="skill_evaluations",
                        to="mi_app.candidate",
                    ),
                ),
            ],
            options={
                "verbose_name": "Evaluación de habilidad",
                "verbose_name_plural": "Evaluaciones de habilidades",
                "ordering": ["-level"],
            },
        ),
    ]
