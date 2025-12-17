from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('didacta', 'remover_unique_together_e_adicionar_constraint'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='justificativa_cancelamento',
            field=models.TextField(blank=True, help_text='Justificativa fornecida ao cancelar a reserva', null=True, verbose_name='Justificativa do Cancelamento'),
        ),
        migrations.AddField(
            model_name='user',
            name='is_admin',
            field=models.BooleanField(default=False, help_text='Marque para dar permissões de administrador', verbose_name='É Administrador'),
        ),
        migrations.AlterField(
            model_name='user',
            name='nome_completo',
            field=models.CharField(max_length=255, verbose_name='Nome de Usuário'),
        ),
        migrations.AlterField(
            model_name='user',
            name='tipo_usuario',
            field=models.CharField(choices=[('aluno', 'Aluno'), ('comunidade_externa', 'Comunidade Externa')], default='aluno', max_length=20, verbose_name='Tipo de Usuário'),
        ),
    ]
