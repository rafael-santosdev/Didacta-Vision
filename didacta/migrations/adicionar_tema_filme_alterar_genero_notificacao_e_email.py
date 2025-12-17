from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('didacta', 'alterar_opcoes_filme_comentario_forum_e_mais'),
    ]

    operations = [
        migrations.AddField(
            model_name='film',
            name='tema',
            field=models.CharField(default='Geral', help_text='Tema que aparecerá em "Explorar por temas"', max_length=100, verbose_name='Tema do filme'),
        ),
        migrations.AlterField(
            model_name='film',
            name='genero',
            field=models.CharField(max_length=100, verbose_name='Gênero'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='tipo',
            field=models.CharField(choices=[('reserva_criada', 'Reserva Criada'), ('reserva_cancelada', 'Reserva Cancelada'), ('reserva_confirmada', 'Reserva Confirmada'), ('sessao_alterada', 'Sessão Alterada'), ('sessao_cancelada', 'Sessão Cancelada'), ('sessao_reagendada', 'Sessão Reagendada'), ('filme_criado', 'Filme Criado'), ('filme_atualizado', 'Filme Atualizado'), ('filme_removido', 'Filme Removido'), ('sessao_criada', 'Sessão Criada'), ('sessao_atualizada', 'Sessão Atualizada'), ('suporte_respondido', 'Suporte Respondido'), ('outro', 'Outro')], default='outro', max_length=20, verbose_name='Tipo'),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, db_index=True, max_length=254, null=True, unique=True, verbose_name='Email'),
        ),
    ]
