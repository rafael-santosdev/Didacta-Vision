import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email')),
                ('nome_completo', models.CharField(max_length=255, verbose_name='Nome Completo')),
                ('telefone', models.CharField(blank=True, max_length=20, verbose_name='Telefone')),
                ('data_nascimento', models.DateField(blank=True, null=True, verbose_name='Data de Nascimento')),
                ('tipo_usuario', models.CharField(choices=[('aluno', 'Aluno'), ('professor', 'Professor'), ('servidor', 'Servidor'), ('comunidade_externa', 'Comunidade Externa'), ('admin', 'Administrador')], default='aluno', max_length=20, verbose_name='Tipo de Usuário')),
                ('token_acesso', models.CharField(blank=True, help_text='Token para usuários da comunidade externa', max_length=100, null=True, verbose_name='Token de Acesso')),
                ('foto_perfil', models.ImageField(blank=True, null=True, upload_to='perfis/', verbose_name='Foto de Perfil')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Usuário',
                'verbose_name_plural': 'Usuários',
                'ordering': ['nome_completo'],
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Film',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=255, unique=True, verbose_name='Título')),
                ('sinopse', models.TextField(verbose_name='Sinopse')),
                ('duracao', models.PositiveIntegerField(help_text='Duração em minutos', verbose_name='Duração (minutos)')),
                ('classificacao', models.CharField(choices=[('L', 'Livre'), ('10', '10 anos'), ('12', '12 anos'), ('14', '14 anos'), ('16', '16 anos'), ('18', '18 anos')], default='L', max_length=2, verbose_name='Classificação Indicativa')),
                ('cartaz', models.ImageField(blank=True, help_text='Imagem do cartaz do filme', null=True, upload_to='filmes/cartazes/', verbose_name='Cartaz')),
                ('cartaz_url', models.URLField(blank=True, help_text='URL alternativa para o cartaz', null=True, verbose_name='URL do Cartaz')),
                ('trailer_url', models.URLField(blank=True, help_text='URL do trailer no YouTube', null=True, unique=True, verbose_name='URL do Trailer (YouTube)')),
                ('genero', models.CharField(blank=True, max_length=100, verbose_name='Gênero')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
            ],
            options={
                'verbose_name': 'Filme',
                'verbose_name_plural': 'Filmes',
                'ordering': ['titulo'],
                'constraints': [models.UniqueConstraint(condition=models.Q(('ativo', True)), fields=('titulo',), name='unique_titulo_ativo')],
            },
        ),
        migrations.CreateModel(
            name='ForumComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('texto', models.TextField(max_length=500, validators=[django.core.validators.MinLengthValidator(10), django.core.validators.MaxLengthValidator(500)], verbose_name='Texto')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('filme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forumcomment_set', to='didacta.film', verbose_name='Filme')),
                ('parent', models.ForeignKey(blank=True, help_text='Comentário ao qual este é uma resposta', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='didacta.forumcomment', verbose_name='Comentário Pai')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forumcomment_set', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Comentário do Fórum',
                'verbose_name_plural': 'Comentários do Fórum',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='HelpTicket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assunto', models.CharField(max_length=255, verbose_name='Assunto')),
                ('mensagem', models.TextField(verbose_name='Mensagem')),
                ('status', models.CharField(choices=[('aberto', 'Aberto'), ('respondido', 'Respondido'), ('fechado', 'Fechado')], default='aberto', max_length=20, verbose_name='Status')),
                ('resposta', models.TextField(blank=True, null=True, verbose_name='Resposta')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='helpticket_set', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Ticket de Suporte',
                'verbose_name_plural': 'Tickets de Suporte',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=255, verbose_name='Título')),
                ('mensagem', models.TextField(verbose_name='Mensagem')),
                ('tipo', models.CharField(choices=[('reserva_criada', 'Reserva Criada'), ('reserva_cancelada', 'Reserva Cancelada'), ('reserva_confirmada', 'Reserva Confirmada'), ('sessao_alterada', 'Sessão Alterada'), ('sessao_cancelada', 'Sessão Cancelada'), ('sessao_reagendada', 'Sessão Reagendada'), ('outro', 'Outro')], default='outro', max_length=20, verbose_name='Tipo')),
                ('lida', models.BooleanField(default=False, verbose_name='Lida')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_set', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Notificação',
                'verbose_name_plural': 'Notificações',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_hora', models.DateTimeField(verbose_name='Data e Hora')),
                ('capacidade_total', models.PositiveIntegerField(default=50, verbose_name='Capacidade Total')),
                ('local', models.CharField(max_length=255, verbose_name='Local')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('filme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='session_set', to='didacta.film', verbose_name='Filme')),
            ],
            options={
                'verbose_name': 'Sessão',
                'verbose_name_plural': 'Sessões',
                'ordering': ['data_hora'],
            },
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('reservado', 'Reservado'), ('cancelado', 'Cancelado'), ('presente', 'Presente'), ('falta_justificada', 'Falta Justificada'), ('falta', 'Falta')], default='reservado', max_length=20, verbose_name='Status')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservation_set', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
                ('sessao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservation_set', to='didacta.session', verbose_name='Sessão')),
            ],
            options={
                'verbose_name': 'Reserva',
                'verbose_name_plural': 'Reservas',
                'ordering': ['-created_at'],
                'unique_together': {('usuario', 'sessao')},
            },
        ),
    ]
