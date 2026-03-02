from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mi_app', '0017_alter_atsclient_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='vacancy',
            name='ai_enabled',
            field=models.BooleanField(
                default=False,
                help_text='Indica si el análisis de CV con IA está activado para esta vacante.',
                verbose_name='IA activada',
            ),
        ),
    ]
