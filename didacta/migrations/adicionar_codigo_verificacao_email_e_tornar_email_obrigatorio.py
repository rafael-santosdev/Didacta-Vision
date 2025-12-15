from django.db import migrations, models
import django.db.models.deletion


def update_null_emails(apps, schema_editor):
    User = apps.get_model('didacta', 'User')
    for user in User.objects.filter(email__isnull=True):
        user.email = f"{user.username}@temp.didactavision.com"
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('didacta', 'adicionar_justificativa_e_is_admin'),
    ]

    operations = [
        migrations.RunPython(update_null_emails, migrations.RunPython.noop),
        migrations.CreateModel(
            name='EmailVerificationCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=6, verbose_name='Código')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('usado', models.BooleanField(default=False, verbose_name='Usado')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='verification_codes', to='didacta.user', verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Código de Verificação',
                'verbose_name_plural': 'Códigos de Verificação',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(db_index=True, max_length=254, unique=True, verbose_name='Email'),
        ),
    ]

