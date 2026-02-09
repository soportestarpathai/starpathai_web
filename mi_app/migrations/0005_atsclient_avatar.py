from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mi_app", "0004_alter_atsclientemailconfig_company_from_email_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="atsclient",
            name="avatar",
            field=models.ImageField(blank=True, null=True, upload_to="ats/avatars/%Y/%m/", verbose_name="Foto de perfil"),
        ),
    ]
