from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("mi_app", "0009_atsform_request_email"),
    ]

    operations = [
        migrations.CreateModel(
            name="ATSNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(choices=[("submission", "Nuevo envío"), ("candidate", "Nuevo candidato"), ("plan", "Plan actualizado"), ("cvs_limit", "Límite de CVs")], default="submission", max_length=30, verbose_name="Tipo")),
                ("title", models.CharField(max_length=200, verbose_name="Título")),
                ("message", models.TextField(blank=True, verbose_name="Mensaje")),
                ("link", models.CharField(blank=True, help_text="URL a la que lleva la notificación", max_length=500, verbose_name="Enlace")),
                ("read", models.BooleanField(default=False, verbose_name="Leída")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="mi_app.atsclient")),
            ],
            options={"verbose_name": "Notificación ATS", "verbose_name_plural": "Notificaciones ATS", "ordering": ["-created_at"]},
        ),
    ]
