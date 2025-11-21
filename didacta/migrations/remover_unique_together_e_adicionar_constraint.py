from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('didacta', 'alterar_gerenciadores_e_email_usuario'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='reservation',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='reservation',
            constraint=models.UniqueConstraint(condition=models.Q(('status__in', ['reservado', 'presente'])), fields=('usuario', 'sessao'), name='unique_reserva_ativa'),
        ),
    ]
