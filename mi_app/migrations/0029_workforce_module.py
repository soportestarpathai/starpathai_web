import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mi_app", "0028_vacancy_public_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscription",
            name="module_workforce",
            field=models.BooleanField(default=False, verbose_name="Módulo Workforce"),
        ),
        migrations.CreateModel(
            name="WorkforceArea",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150, verbose_name="Nombre")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="workforce_areas", to="mi_app.atsclient")),
            ],
            options={
                "verbose_name": "Área Workforce",
                "verbose_name_plural": "Áreas Workforce",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="WorkforcePosition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150, verbose_name="Nombre")),
                ("salary_min", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Salario mínimo")),
                ("salary_max", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Salario máximo")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("area", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="positions", to="mi_app.workforcearea")),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="workforce_positions", to="mi_app.atsclient")),
            ],
            options={
                "verbose_name": "Puesto Workforce",
                "verbose_name_plural": "Puestos Workforce",
                "ordering": ["area__name", "name"],
            },
        ),
        migrations.CreateModel(
            name="WorkforcePlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="ID público")),
                ("current_staff", models.PositiveIntegerField(default=0, verbose_name="Personal actual")),
                ("required_staff", models.PositiveIntegerField(default=0, verbose_name="Personal requerido")),
                ("turnover_rate", models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name="Rotación (%)")),
                ("open_vacancies", models.PositiveIntegerField(default=0, verbose_name="Vacantes abiertas")),
                ("priority", models.CharField(choices=[("baja", "Baja"), ("media", "Media"), ("alta", "Alta"), ("critica", "Crítica")], default="media", max_length=50, verbose_name="Prioridad")),
                ("estimated_budget", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Presupuesto estimado")),
                ("status", models.CharField(choices=[("borrador", "Borrador"), ("pendiente", "Pendiente de aprobación"), ("aprobado", "Aprobado"), ("rechazado", "Rechazado"), ("convertido_vacante", "Convertido en vacante")], default="pendiente", max_length=50, verbose_name="Estado")),
                ("executive_justification", models.TextField(blank=True, verbose_name="Justificación ejecutiva")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("area", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="plans", to="mi_app.workforcearea")),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="workforce_plans", to="mi_app.atsclient")),
                ("position", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="plans", to="mi_app.workforceposition")),
            ],
            options={
                "verbose_name": "Plan Workforce",
                "verbose_name_plural": "Planes Workforce",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddField(
            model_name="vacancy",
            name="openings",
            field=models.PositiveIntegerField(default=1, verbose_name="Plazas"),
        ),
        migrations.AddField(
            model_name="vacancy",
            name="salary_min",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="Salario mínimo"),
        ),
        migrations.AddField(
            model_name="vacancy",
            name="salary_max",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="Salario máximo"),
        ),
        migrations.AddField(
            model_name="vacancy",
            name="source",
            field=models.CharField(choices=[("manual", "Manual"), ("workforce", "Workforce")], default="manual", max_length=30, verbose_name="Origen"),
        ),
        migrations.AddField(
            model_name="vacancy",
            name="workforce_plan",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_vacancies", to="mi_app.workforceplan"),
        ),
        migrations.AddConstraint(
            model_name="workforcearea",
            constraint=models.UniqueConstraint(fields=("client", "name"), name="unique_workforce_area_client_name"),
        ),
        migrations.AddConstraint(
            model_name="workforceposition",
            constraint=models.UniqueConstraint(fields=("client", "area", "name"), name="unique_workforce_position_client_area_name"),
        ),
    ]
