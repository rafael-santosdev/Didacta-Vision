from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('didacta', 'adicionar_codigo_verificacao_email_e_tornar_email_obrigatorio'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='film',
            options={'ordering': ['titulo'], 'permissions': [('can_manage_films', 'Pode gerenciar filmes'), ('can_view_films', 'Pode visualizar filmes')], 'verbose_name': 'Filme', 'verbose_name_plural': 'Filmes'},
        ),
        migrations.AlterModelOptions(
            name='forumcomment',
            options={'ordering': ['-created_at'], 'permissions': [('can_moderate_comments', 'Pode moderar comentários')], 'verbose_name': 'Comentário do Fórum', 'verbose_name_plural': 'Comentários do Fórum'},
        ),
        migrations.AlterModelOptions(
            name='helpticket',
            options={'ordering': ['-created_at'], 'permissions': [('can_manage_tickets', 'Pode gerenciar tickets de suporte'), ('can_view_tickets', 'Pode visualizar tickets de suporte')], 'verbose_name': 'Ticket de Suporte', 'verbose_name_plural': 'Tickets de Suporte'},
        ),
        migrations.AlterModelOptions(
            name='notification',
            options={'ordering': ['-created_at'], 'permissions': [('can_view_notifications', 'Pode visualizar notificações')], 'verbose_name': 'Notificação', 'verbose_name_plural': 'Notificações'},
        ),
        migrations.AlterModelOptions(
            name='reservation',
            options={'ordering': ['-created_at'], 'permissions': [('can_manage_reservations', 'Pode gerenciar reservas'), ('can_view_reservations', 'Pode visualizar reservas')], 'verbose_name': 'Reserva', 'verbose_name_plural': 'Reservas'},
        ),
        migrations.AlterModelOptions(
            name='session',
            options={'ordering': ['data_hora'], 'permissions': [('can_manage_sessions', 'Pode gerenciar sessões'), ('can_view_sessions', 'Pode visualizar sessões')], 'verbose_name': 'Sessão', 'verbose_name_plural': 'Sessões'},
        ),
    ]
