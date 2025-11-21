from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import (
    User, Film, Session, Reservation, ForumComment, HelpTicket
)

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'required': True})
    )
    nome_completo = forms.CharField(
        label='Nome de Usuário',
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    telefone = forms.CharField(
        label='Telefone',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    data_nascimento = forms.DateField(
        label='Data de Nascimento',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    tipo_usuario = forms.ChoiceField(
        label='Tipo de Usuário',
        choices=User.TIPO_USUARIO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('email', 'nome_completo', 'telefone', 'data_nascimento', 'tipo_usuario', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if User.objects.filter(email=email).exists():
                raise ValidationError('Este email já está cadastrado.')
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            if len(password1) < 8:
                raise ValidationError('A senha deve ter pelo menos 8 caracteres.')
            if not any(c.isalpha() for c in password1):
                raise ValidationError('A senha deve conter pelo menos uma letra.')
        return password1

    def save(self, commit=True):
        user = super().save(commit=False)
        if not user.username:
            user.username = user.email if user.email else user.nome_completo.lower().replace(' ', '_')
        if commit:
            user.save()
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('nome_completo', 'telefone', 'data_nascimento', 'foto_perfil')
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'form-control'}),
        }

class PasswordChangeForm(forms.Form):
    senha_atual = forms.CharField(
        label='Senha Atual',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    nova_senha = forms.CharField(
        label='Nova Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'id_nova_senha'}),
        min_length=8
    )
    confirmar_senha = forms.CharField(
        label='Confirmar Nova Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_senha_atual(self):
        senha_atual = self.cleaned_data.get('senha_atual')
        if not self.user.check_password(senha_atual):
            raise ValidationError('Senha atual incorreta.')
        return senha_atual

    def clean_nova_senha(self):
        nova_senha = self.cleaned_data.get('nova_senha')
        if nova_senha:
            if len(nova_senha) < 8:
                raise ValidationError('A senha deve ter pelo menos 8 caracteres.')
            if not any(c.isalpha() for c in nova_senha):
                raise ValidationError('A senha deve conter pelo menos uma letra.')
        return nova_senha

    def clean(self):
        cleaned_data = super().clean()
        nova_senha = cleaned_data.get('nova_senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')

        if nova_senha and confirmar_senha:
            if nova_senha != confirmar_senha:
                raise ValidationError('As senhas não coincidem.')

        return cleaned_data

class FilmForm(forms.ModelForm):
    class Meta:
        model = Film
        fields = ('titulo', 'sinopse', 'duracao', 'classificacao', 'cartaz', 'cartaz_url', 'trailer_url', 'genero', 'ativo')
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'sinopse': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'duracao': forms.NumberInput(attrs={'class': 'form-control'}),
            'classificacao': forms.Select(attrs={'class': 'form-control'}),
            'cartaz': forms.FileInput(attrs={'class': 'form-control'}),
            'cartaz_url': forms.URLInput(attrs={'class': 'form-control'}),
            'trailer_url': forms.URLInput(attrs={'class': 'form-control'}),
            'genero': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_titulo(self):
        titulo = self.cleaned_data.get('titulo')
        if self.instance.pk:
            if Film.objects.filter(titulo=titulo, ativo=True).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Já existe um filme ativo com este título.')
        else:
            if Film.objects.filter(titulo=titulo, ativo=True).exists():
                raise ValidationError('Já existe um filme ativo com este título.')
        return titulo

    def clean_trailer_url(self):
        trailer_url = self.cleaned_data.get('trailer_url')
        if trailer_url:
            if self.instance.pk:
                if Film.objects.filter(trailer_url=trailer_url).exclude(pk=self.instance.pk).exists():
                    raise ValidationError('Já existe um filme com esta URL de trailer.')
            else:
                if Film.objects.filter(trailer_url=trailer_url).exists():
                    raise ValidationError('Já existe um filme com esta URL de trailer.')
        return trailer_url

class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ('filme', 'data_hora', 'capacidade_total', 'local', 'ativo')
        widgets = {
            'filme': forms.Select(attrs={'class': 'form-control'}),
            'data_hora': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'capacidade_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'local': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ('sessao',)
        widgets = {
            'sessao': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        sessao = cleaned_data.get('sessao')

        if sessao and self.user:
            if not sessao.tem_vagas():
                raise ValidationError('Não há vagas disponíveis para esta sessão.')

            if Reservation.objects.filter(
                usuario=self.user,
                sessao=sessao,
                status__in=['reservado', 'presente']
            ).exists():
                raise ValidationError('Você já possui uma reserva ativa para esta sessão.')

        return cleaned_data

class ForumCommentForm(forms.ModelForm):
    class Meta:
        model = ForumComment
        fields = ('texto', 'parent')
        widgets = {
            'texto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'maxlength': 500,
                'placeholder': 'Digite seu comentário (máximo 500 caracteres)'
            }),
            'parent': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.filme = kwargs.pop('filme', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        texto = cleaned_data.get('texto')

        if texto and len(texto) < 10:
            raise ValidationError('O comentário deve ter no mínimo 10 caracteres.')

        if texto and len(texto) > 500:
            raise ValidationError('O comentário deve ter no máximo 500 caracteres.')

        if self.user and self.filme:
            comment = ForumComment(filme=self.filme, usuario=self.user)
            if not comment.pode_comentar(self.user):
                raise ValidationError(
                    'Você precisa ter presença confirmada ou falta justificada em uma sessão deste filme para comentar.'
                )

        return cleaned_data

class HelpTicketForm(forms.ModelForm):
    class Meta:
        model = HelpTicket
        fields = ('assunto', 'mensagem')
        widgets = {
            'assunto': forms.TextInput(attrs={'class': 'form-control'}),
            'mensagem': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

class ReservationCancelForm(forms.Form):
    justificativa = forms.CharField(
        label='Justificativa do Cancelamento',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Opcional: Informe o motivo do cancelamento...'
        }),
        help_text='Opcional: Informe o motivo do cancelamento'
    )

