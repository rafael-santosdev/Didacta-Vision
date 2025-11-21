from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('didacta', 'alterar_email_usuario'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
            ],
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, db_index=True, max_length=254, null=True, unique=True, verbose_name='Email'),
        ),
    ]
