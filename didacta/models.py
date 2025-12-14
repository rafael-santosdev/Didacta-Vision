from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings

class UserManager(BaseUserManager):

    def create_user(self, username=None, email=None, password=None, **extra_fields):
        if not username and not email:
            raise ValueError('É necessário fornecer username ou email')

        if not username:
            username = email if email else extra_fields.get('nome_completo', 'user').lower().replace(' ', '_')

        email = self.normalize_email(email) if email else None
        if email and self.model.objects.filter(email=email).exists():
            raise ValueError('Já existe um usuário com este email.')

        user = self.model(username=username, email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('tipo_usuario', 'admin')

        username = extra_fields.pop('username', None)

        if not username and not email:
            nome_completo = extra_fields.get('nome_completo')
            if nome_completo:
                username = nome_completo.lower().replace(' ', '_')
            else:
                username = 'admin'

        if not username:
            username = email if email else 'admin'

        return self.create_user(username=username, email=email, password=password, **extra_fields)

class User(AbstractUser):
    TIPO_USUARIO_CHOICES = [
        ('aluno', 'Aluno'),
        ('comunidade_externa', 'Comunidade Externa'),
    ]

    email = models.EmailField('Email', unique=True, db_index=True, blank=True, null=True)
    nome_completo = models.CharField('Nome de Usuário', max_length=255)
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    data_nascimento = models.DateField('Data de Nascimento', null=True, blank=True)
    tipo_usuario = models.CharField(
        'Tipo de Usuário',
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        default='aluno'
    )
    is_admin = models.BooleanField('É Administrador', default=False, help_text='Marque para dar permissões de administrador')

    token_acesso = models.CharField(
        'Token de Acesso',
        max_length=100,
        blank=True,
        null=True,
        help_text='Token para usuários da comunidade externa'
    )
    foto_perfil = models.ImageField(
        'Foto de Perfil',
        upload_to='perfis/',
        blank=True,
        null=True
    )

    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome_completo']

    objects = UserManager()

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['nome_completo']

    def __str__(self):
        email_str = self.email if self.email else "sem email"
        return f"{self.nome_completo} ({email_str})"

    def is_admin_or_professor(self):
        return self.is_admin or self.is_superuser

class Film(models.Model):
    CLASSIFICACAO_CHOICES = [
        ('L', 'Livre'),
        ('10', '10 anos'),
        ('12', '12 anos'),
        ('14', '14 anos'),
        ('16', '16 anos'),
        ('18', '18 anos'),
    ]

    titulo = models.CharField('Título', max_length=255, unique=True)
    sinopse = models.TextField('Sinopse')
    duracao = models.PositiveIntegerField('Duração (minutos)', help_text='Duração em minutos')
    classificacao = models.CharField(
        'Classificação Indicativa',
        max_length=2,
        choices=CLASSIFICACAO_CHOICES,
        default='L'
    )
    cartaz = models.ImageField(
        'Cartaz',
        upload_to='filmes/cartazes/',
        blank=True,
        null=True,
        help_text='Imagem do cartaz do filme'
    )
    cartaz_url = models.URLField(
        'URL do Cartaz',
        blank=True,
        null=True,
        help_text='URL alternativa para o cartaz'
    )
    trailer_url = models.URLField(
        'URL do Trailer (YouTube)',
        unique=True,
        blank=True,
        null=True,
        help_text='URL do trailer no YouTube'
    )
    genero = models.CharField('Gênero', max_length=100, blank=False)
    tema = models.CharField('Tema do filme', max_length=100, blank=False, default='Geral', help_text='Tema que aparecerá em "Explorar por temas"')
    ativo = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Filme'
        verbose_name_plural = 'Filmes'
        ordering = ['titulo']
        permissions = [
            ('can_manage_films', 'Pode gerenciar filmes'),
            ('can_view_films', 'Pode visualizar filmes'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['titulo'],
                condition=models.Q(ativo=True),
                name='unique_titulo_ativo'
            )
        ]

    def __str__(self):
        return self.titulo

    def clean(self):
        if self.pk:
            from django.utils import timezone
            if not self.ativo:
                if self.session_set.filter(data_hora__gt=timezone.now(), ativo=True).exists():
                    raise ValidationError('Não é possível desativar filme com sessões futuras.')
                if self.forumcomment_set.filter(ativo=True).exists():
                    raise ValidationError('Não é possível desativar filme com comentários ativos no fórum.')

    def pode_ser_deletado(self):
        from django.utils import timezone
        tem_sessoes_futuras = self.session_set.filter(
            data_hora__gt=timezone.now(),
            ativo=True
        ).exists()
        tem_comentarios_ativos = self.forumcomment_set.filter(ativo=True).exists()
        return not (tem_sessoes_futuras or tem_comentarios_ativos)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('didacta:film_detail', kwargs={'pk': self.pk})

class Session(models.Model):
    filme = models.ForeignKey(
        Film,
        on_delete=models.CASCADE,
        verbose_name='Filme',
        related_name='session_set'
    )
    data_hora = models.DateTimeField('Data e Hora')
    capacidade_total = models.PositiveIntegerField('Capacidade Total', default=50)
    local = models.CharField('Local', max_length=255)
    ativo = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Sessão'
        verbose_name_plural = 'Sessões'
        ordering = ['data_hora']
        permissions = [
            ('can_manage_sessions', 'Pode gerenciar sessões'),
            ('can_view_sessions', 'Pode visualizar sessões'),
        ]

    def __str__(self):
        return f"{self.filme.titulo} - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"

    @property
    def vagas_disponiveis(self):
        reservas_ativas = self.reservation_set.filter(
            status__in=['reservado', 'presente']
        ).count()
        return max(0, self.capacidade_total - reservas_ativas)

    @property
    def esta_cheia(self):
        return self.vagas_disponiveis == 0

    def tem_vagas(self):
        return self.vagas_disponiveis > 0

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('didacta:film_detail', kwargs={'pk': self.filme.pk})

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('reservado', 'Reservado'),
        ('cancelado', 'Cancelado'),
        ('presente', 'Presente'),
        ('falta_justificada', 'Falta Justificada'),
        ('falta', 'Falta'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Usuário',
        related_name='reservation_set'
    )
    sessao = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        verbose_name='Sessão',
        related_name='reservation_set'
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='reservado'
    )
    justificativa_cancelamento = models.TextField(
        'Justificativa do Cancelamento',
        blank=True,
        null=True,
        help_text='Justificativa fornecida ao cancelar a reserva'
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-created_at']
        permissions = [
            ('can_manage_reservations', 'Pode gerenciar reservas'),
            ('can_view_reservations', 'Pode visualizar reservas'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'sessao'],
                condition=models.Q(status__in=['reservado', 'presente']),
                name='unique_reserva_ativa'
            )
        ]

    def __str__(self):
        usuario_nome = self.usuario.nome_completo if self.usuario else "Usuário removido"
        sessao_str = str(self.sessao) if self.sessao else "Sessão removida"
        return f"{usuario_nome} - {sessao_str} ({self.get_status_display()})"

    def clean(self):
        usuario = getattr(self, 'usuario', None)
        sessao = getattr(self, 'sessao', None)

        if self.status == 'reservado' and usuario and sessao:
            if not sessao.tem_vagas():
                raise ValidationError('Não há vagas disponíveis para esta sessão.')

            if self.pk:
                existing = Reservation.objects.filter(
                    usuario=usuario,
                    sessao=sessao,
                    status__in=['reservado', 'presente']
                ).exclude(pk=self.pk)
            else:
                existing = Reservation.objects.filter(
                    usuario=usuario,
                    sessao=sessao,
                    status__in=['reservado', 'presente']
                )

            if existing.exists():
                raise ValidationError('Você já possui uma reserva ativa para esta sessão.')

class ForumComment(models.Model):
    filme = models.ForeignKey(
        Film,
        on_delete=models.CASCADE,
        verbose_name='Filme',
        related_name='forumcomment_set'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Usuário',
        related_name='forumcomment_set'
    )
    texto = models.TextField(
        'Texto',
        max_length=500,
        validators=[MinLengthValidator(10), MaxLengthValidator(500)]
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='Comentário Pai',
        help_text='Comentário ao qual este é uma resposta'
    )
    ativo = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Comentário do Fórum'
        verbose_name_plural = 'Comentários do Fórum'
        ordering = ['-created_at']
        permissions = [
            ('can_moderate_comments', 'Pode moderar comentários'),
        ]

    def __str__(self):
        preview = self.texto[:50] + '...' if len(self.texto) > 50 else self.texto
        return f"{self.usuario.nome_completo} - {self.filme.titulo}: {preview}"

    def pode_comentar(self, usuario):
        if not usuario.is_authenticated:
            return False

        sessoes_do_filme = self.filme.session_set.all()
        reservas_validas = Reservation.objects.filter(
            usuario=usuario,
            sessao__in=sessoes_do_filme,
            status__in=['presente', 'falta_justificada']
        ).exists()

        return reservas_validas or usuario.is_admin_or_professor()

class Notification(models.Model):
    TIPO_CHOICES = [
        ('reserva_criada', 'Reserva Criada'),
        ('reserva_cancelada', 'Reserva Cancelada'),
        ('reserva_confirmada', 'Reserva Confirmada'),
        ('sessao_alterada', 'Sessão Alterada'),
        ('sessao_cancelada', 'Sessão Cancelada'),
        ('sessao_reagendada', 'Sessão Reagendada'),
        ('filme_criado', 'Filme Criado'),
        ('filme_atualizado', 'Filme Atualizado'),
        ('filme_removido', 'Filme Removido'),
        ('sessao_criada', 'Sessão Criada'),
        ('sessao_atualizada', 'Sessão Atualizada'),
        ('suporte_respondido', 'Suporte Respondido'),
        ('outro', 'Outro'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Usuário',
        related_name='notification_set'
    )
    titulo = models.CharField('Título', max_length=255)
    mensagem = models.TextField('Mensagem')
    tipo = models.CharField(
        'Tipo',
        max_length=20,
        choices=TIPO_CHOICES,
        default='outro'
    )
    lida = models.BooleanField('Lida', default=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-created_at']
        permissions = [
            ('can_view_notifications', 'Pode visualizar notificações'),
        ]

    def __str__(self):
        return f"{self.usuario.nome_completo} - {self.titulo}"
    
    def get_categoria_display(self):
        """Retorna 'Filmes', 'Sessões', 'Suporte' ou 'Outro' baseado no tipo da notificação"""
        tipos_filmes = ['filme_criado', 'filme_atualizado', 'filme_removido']
        tipos_sessoes = ['sessao_criada', 'sessao_atualizada', 'sessao_cancelada', 'sessao_alterada', 
                        'sessao_reagendada', 'reserva_criada', 'reserva_cancelada', 'reserva_confirmada']
        tipos_suporte = ['suporte_respondido']
        
        if self.tipo in tipos_filmes:
            return 'Filmes'
        elif self.tipo in tipos_sessoes:
            return 'Sessões'
        elif self.tipo in tipos_suporte:
            return 'Suporte'
        else:
            return 'Outro'

class HelpTicket(models.Model):
    STATUS_CHOICES = [
        ('aberto', 'Aberto'),
        ('respondido', 'Respondido'),
        ('fechado', 'Fechado'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuário',
        related_name='helpticket_set'
    )
    assunto = models.CharField('Assunto', max_length=255)
    mensagem = models.TextField('Mensagem')
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='aberto'
    )
    resposta = models.TextField('Resposta', blank=True, null=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Ticket de Suporte'
        verbose_name_plural = 'Tickets de Suporte'
        ordering = ['-created_at']
        permissions = [
            ('can_manage_tickets', 'Pode gerenciar tickets de suporte'),
            ('can_view_tickets', 'Pode visualizar tickets de suporte'),
        ]

    def __str__(self):
        return f"{self.assunto} - {self.get_status_display()}"

class EmailVerificationCode(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Usuário',
        related_name='verification_codes'
    )
    codigo = models.CharField('Código', max_length=6)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    usado = models.BooleanField('Usado', default=False)

    class Meta:
        verbose_name = 'Código de Verificação'
        verbose_name_plural = 'Códigos de Verificação'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.usuario.email} - {self.codigo} ({'Usado' if self.usado else 'Ativo'})"

    def is_valid(self):
        from django.utils import timezone
        from datetime import timedelta

        if self.usado:
            return False

        expiracao = self.created_at + timedelta(minutes=10)
        return timezone.now() <= expiracao
