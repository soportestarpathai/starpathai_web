from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mi_app", "0008_atsform_request_cv"),
    ]

    operations = [
        migrations.AddField(
            model_name="atsform",
            name="request_email",
            field=models.BooleanField(
                default=True,
                help_text="Si está activo, el formulario incluirá un campo de correo (o usará el que ya tengas).",
                verbose_name="Solicitar correo electrónico",
            ),
        ),
    ]
