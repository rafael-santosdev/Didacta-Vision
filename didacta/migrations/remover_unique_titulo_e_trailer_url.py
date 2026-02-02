from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('didacta', '0001_acesso_provisorio'),
    ]

    operations = [
        migrations.AlterField(
            model_name='film',
            name='titulo',
            field=models.CharField(max_length=255, verbose_name='Título'),
        ),
        migrations.AlterField(
            model_name='film',
            name='trailer_url',
            field=models.URLField(
                blank=True,
                help_text='URL do trailer no YouTube',
                null=True,
                verbose_name='URL do Trailer (YouTube)',
            ),
        ),
    ]
