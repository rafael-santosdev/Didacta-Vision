from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Film, Session, Reservation, ForumComment, Notification, HelpTicket,
    EmailVerificationCode
)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('nome_completo', 'email', 'tipo_usuario', 'is_admin', 'is_active', 'created_at')
    list_filter = ('tipo_usuario', 'is_admin', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'nome_completo', 'username')
    ordering = ('nome_completo',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {
            'fields': ('nome_completo', 'email', 'telefone', 'data_nascimento', 'foto_perfil')
        }),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Informações Adicionais', {
            'fields': ('tipo_usuario', 'is_admin', 'token_acesso', 'last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('nome_completo', 'password1', 'password2'),
        }),
        ('Informações Adicionais', {
            'fields': ('username', 'email', 'telefone', 'data_nascimento', 'tipo_usuario', 'is_admin', 'token_acesso', 'foto_perfil')
        }),
    )

@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'classificacao', 'duracao', 'genero', 'ativo', 'created_at')
    list_filter = ('ativo', 'classificacao', 'genero')
    search_fields = ('titulo', 'sinopse', 'genero')
    ordering = ('titulo',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('filme', 'data_hora', 'local', 'capacidade_total', 'ativo', 'created_at')
    list_filter = ('ativo', 'data_hora')
    search_fields = ('filme__titulo', 'local')
    ordering = ('-data_hora',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'data_hora'

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'sessao', 'status', 'justificativa_cancelamento', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('usuario__nome_completo', 'usuario__email', 'sessao__filme__titulo')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ForumComment)
class ForumCommentAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'filme', 'texto_preview', 'ativo', 'created_at')
    list_filter = ('ativo', 'created_at')
    search_fields = ('usuario__nome_completo', 'filme__titulo', 'texto')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    def texto_preview(self, obj):
        return obj.texto[:50] + '...' if len(obj.texto) > 50 else obj.texto
    texto_preview.short_description = 'Texto'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'titulo', 'tipo', 'lida', 'created_at')
    list_filter = ('tipo', 'lida', 'created_at')
    search_fields = ('usuario__nome_completo', 'titulo', 'mensagem')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

@admin.register(HelpTicket)
class HelpTicketAdmin(admin.ModelAdmin):
    list_display = ('assunto', 'usuario', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('assunto', 'mensagem', 'usuario__nome_completo')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'codigo', 'usado', 'created_at')
    list_filter = ('usado', 'created_at')
    search_fields = ('usuario__nome_completo', 'usuario__email', 'codigo')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
