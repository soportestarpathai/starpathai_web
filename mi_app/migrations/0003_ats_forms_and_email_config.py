# ATS: Formularios (crear/enviar/recibir) + Configuración de correo

import uuid
from django.db import migrations, models
import django.db.models.deletion


def generate_uuids_for_forms(apps, schema_editor):
    ATSForm = apps.get_model("mi_app", "ATSForm")
    for f in ATSForm.objects.all():
        f.uuid = uuid.uuid4()
        f.save(update_fields=["uuid"])


class Migration(migrations.Migration):

    dependencies = [
        ("mi_app", "0002_ats_subscription_vacancy_candidate_skills"),
    ]

    operations = [
        migrations.CreateModel(
            name="ATSClientEmailConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("notification_email", models.EmailField(blank=True, help_text="Aquí recibirás avisos de nuevas respuestas a formularios y candidatos.", max_length=254, verbose_name="Correo de notificaciones")),
                ("company_from_email", models.EmailField(blank=True, help_text="Correo con el que se enviarán mensajes a candidatos (ej. noreply@tuempresa.com).", max_length=254, verbose_name="Correo de envío (empresa)")),
                ("company_from_name", models.CharField(blank=True, help_text="Nombre que verán los candidatos (ej. Recursos Humanos - Mi Empresa).", max_length=150, verbose_name="Nombre del remitente")),
                ("smtp_host", models.CharField(blank=True, max_length=255, verbose_name="Servidor SMTP")),
                ("smtp_port", models.PositiveIntegerField(blank=True, default=587, null=True, verbose_name="Puerto SMTP")),
                ("smtp_user", models.CharField(blank=True, max_length=255, verbose_name="Usuario SMTP")),
                ("smtp_password_encrypted", models.CharField(blank=True, max_length=255, verbose_name="Contraseña SMTP (encriptada)")),
                ("smtp_use_tls", models.BooleanField(default=True, verbose_name="Usar TLS")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="email_config", to="mi_app.atsclient")),
            ],
            options={"verbose_name": "Configuración de correo ATS", "verbose_name_plural": "Configuraciones de correo ATS"},
        ),
        migrations.CreateModel(
            name="ATSForm",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, verbose_name="Nombre del formulario")),
                ("slug", models.SlugField(blank=True, max_length=100, verbose_name="Slug")),
                ("description", models.TextField(blank=True, verbose_name="Descripción (instrucciones para el candidato)")),
                ("is_active", models.BooleanField(default=True, verbose_name="Activo")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("uuid", models.UUIDField(blank=True, editable=False, null=True, unique=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ats_forms", to="mi_app.atsclient")),
                ("vacancy", models.ForeignKey(blank=True, help_text="Vacante asociada (opcional).", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ats_forms", to="mi_app.vacancy")),
            ],
            options={"verbose_name": "Formulario ATS", "verbose_name_plural": "Formularios ATS", "ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="ATSFormField",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("label", models.CharField(max_length=200, verbose_name="Etiqueta")),
                ("field_type", models.CharField(choices=[("text", "Texto corto"), ("email", "Correo electrónico"), ("phone", "Teléfono"), ("textarea", "Texto largo (párrafo)"), ("file", "Archivo (CV/PDF)")], default="text", max_length=20, verbose_name="Tipo")),
                ("required", models.BooleanField(default=True, verbose_name="Obligatorio")),
                ("order", models.PositiveSmallIntegerField(default=0, verbose_name="Orden")),
                ("placeholder", models.CharField(blank=True, max_length=200, verbose_name="Placeholder")),
                ("form", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fields", to="mi_app.atsform")),
            ],
            options={"verbose_name": "Campo de formulario", "verbose_name_plural": "Campos de formulario", "ordering": ["order", "id"]},
        ),
        migrations.CreateModel(
            name="ATSFormSubmission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("payload", models.JSONField(default=dict, verbose_name="Datos enviados")),
                ("submitter_email", models.EmailField(blank=True, max_length=254, verbose_name="Correo del remitente")),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("candidate", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="form_submissions", to="mi_app.candidate")),
                ("form", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="submissions", to="mi_app.atsform")),
            ],
            options={"verbose_name": "Envío de formulario", "verbose_name_plural": "Envíos de formularios", "ordering": ["-submitted_at"]},
        ),
        migrations.CreateModel(
            name="ATSFormSubmissionFile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="ats/form_uploads/%Y/%m/", verbose_name="Archivo")),
                ("original_name", models.CharField(blank=True, max_length=255, verbose_name="Nombre original")),
                ("form_field", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="submission_files", to="mi_app.atsformfield")),
                ("submission", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="files", to="mi_app.atsformsubmission")),
            ],
            options={"verbose_name": "Archivo de envío", "verbose_name_plural": "Archivos de envíos"},
        ),
        migrations.AddConstraint(
            model_name="atsform",
            constraint=models.UniqueConstraint(fields=("client", "slug"), name="unique_client_form_slug"),
        ),
    ]
