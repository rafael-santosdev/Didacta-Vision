from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings

from .models import (
    User, Film, Session, Reservation, ForumComment, Notification, HelpTicket,
    EmailVerificationCode
)
from .formularios import (
    CustomUserCreationForm, UserUpdateForm, PasswordChangeForm,
    FilmForm, SessionForm, ReservationForm, ForumCommentForm, HelpTicketForm,
    ReservationCancelForm
)
from .email_utils import send_verification_email

def register_view(request):
    if request.user.is_authenticated:
        return redirect('didacta:index')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            user.refresh_from_db()
            
            import random
            codigo = ''.join([str(random.randint(0, 9)) for _ in range(6)])

            EmailVerificationCode.objects.create(
                usuario=user,
                codigo=codigo
            )

            subject = 'Código de Verificação - Didacta Vision'
            body = (
                f'Olá {user.nome_completo},\n\nBem-vindo ao Didacta Vision!\n\n'
                f'Seu código de verificação é: {codigo}\n\n'
                f'Este código é válido por 10 minutos.\n\n'
                'Use este código para verificar sua conta e fazer login.'
            )
            recipient_list = [user.email] if user.email else []
            enviado, erro = send_verification_email(recipient_list, subject, body)

            if enviado:
                messages.success(
                    request,
                    f'Conta criada com sucesso! Código de verificação enviado para {user.email}. '
                    'Se não receber em 2–3 minutos, confira a pasta de spam ou use o código temporário na próxima tela.'
                )
                request.session.pop('email_entrega_falhou', None)
            else:
                request.session['email_entrega_falhou'] = True
                if user.email:
                    msg = (
                        'Conta criada! O e-mail pode não ter sido entregue. '
                        'Use o código temporário na próxima tela para acessar.'
                    )
                    if settings.DEBUG and erro:
                        msg += f' (Detalhe: {erro})'
                    messages.warning(request, msg)
                else:
                    messages.success(request, f'Conta criada com sucesso! Seu código de verificação é: {codigo}')

            request.session['verification_user_id'] = user.id
            return redirect('didacta:verify_code')
    else:
        form = CustomUserCreationForm()

    return render(request, 'didacta/autenticacao/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('didacta:index')

    if request.method == 'POST':
        nome_ou_email = request.POST.get('email')
        password = request.POST.get('password')

        if not nome_ou_email:
            messages.error(request, 'Nome ou email é obrigatório para login.')
            return render(request, 'didacta/autenticacao/login.html')

        user_found = User.objects.filter(username__iexact=nome_ou_email).first()
        if not user_found:
            user_found = User.objects.filter(nome_completo__iexact=nome_ou_email).first()
        if not user_found:
            user_found = User.objects.filter(email__iexact=nome_ou_email).first()
        
        if user_found and user_found.check_password(password):
            if not user_found.is_active:
                messages.error(request, 'Sua conta ainda não foi verificada. Complete o processo de verificação para fazer login.')
                return render(request, 'didacta/autenticacao/login.html')
            
            login(request, user_found, backend='didacta.autenticacao_backend.NomeOrEmailBackend')
            messages.success(request, f'Bem-vindo, {user_found.nome_completo}!')
            next_url = request.GET.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('didacta:index')
        else:
            messages.error(request, 'Dados de conta de usuário não encontrados.')

    return render(request, 'didacta/autenticacao/login.html')

def verify_code_view(request):
    user_id = request.session.get('verification_user_id')

    if not user_id:
        messages.error(request, 'Sessão expirada. Por favor, faça login novamente.')
        return redirect('didacta:login')

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Usuário não encontrado.')
        del request.session['verification_user_id']
        return redirect('didacta:login')

    import random
    codigo_temporario = request.session.get('codigo_temporario')
    if not codigo_temporario:
        codigo_temporario = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        request.session['codigo_temporario'] = codigo_temporario

    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        usar_acesso_provisorio = request.POST.get('acesso_provisorio') == '1'

        if not codigo:
            messages.error(request, 'Por favor, informe o código de verificação.')
            return render(request, 'didacta/autenticacao/verify_code.html', {
                'user': user,
                'codigo_temporario': codigo_temporario
            })

        if usar_acesso_provisorio and codigo == codigo_temporario:
            from datetime import timedelta
            user.is_active = True
            user.acesso_provisorio_expira = timezone.now() + timedelta(hours=1)
            user.save()
            
            del request.session['verification_user_id']
            if 'codigo_temporario' in request.session:
                del request.session['codigo_temporario']
            
            login(request, user, backend='didacta.autenticacao_backend.NomeOrEmailBackend')
            messages.warning(request, 
                'Acesso provisório ativado! Você tem aproximadamente 1 hora para usar o sistema. '
                'Para continuar usando após esse período, verifique seu e-mail.'
            )
            return redirect('didacta:index')

        codigo_obj = EmailVerificationCode.objects.filter(
            usuario=user,
            codigo=codigo,
            usado=False
        ).order_by('-created_at').first()

        if codigo_obj and codigo_obj.is_valid():
            codigo_obj.usado = True
            codigo_obj.save()
            
            user.is_active = True
            user.email_verificado = True
            user.acesso_provisorio_expira = None
            user.save()

            del request.session['verification_user_id']
            if 'codigo_temporario' in request.session:
                del request.session['codigo_temporario']

            messages.success(request, 'E-mail verificado com sucesso! Faça login com suas credenciais.')
            return redirect('didacta:login')
        else:
            messages.error(request, 'Código inválido ou expirado. Por favor, tente novamente.')

    email_entrega_falhou = request.session.pop('email_entrega_falhou', False)

    return render(request, 'didacta/autenticacao/verify_code.html', {
        'user': user,
        'codigo_temporario': codigo_temporario,
        'email_entrega_falhou': email_entrega_falhou,
    })

def cancel_verification_view(request):
    user_id = request.session.get('verification_user_id')
    
    if user_id:
        try:
            user = User.objects.get(pk=user_id)
            if not user.is_active:
                user.delete()
        except User.DoesNotExist:
            pass
        
        if 'verification_user_id' in request.session:
            del request.session['verification_user_id']
        if 'codigo_temporario' in request.session:
            del request.session['codigo_temporario']
    
    messages.warning(request, 'Processo de cadastro cancelado. A verificação não foi concluída.')
    return redirect('didacta:login')

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'Você foi desconectado com sucesso.')
    return redirect('didacta:index')

def password_reset_request(request):
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, 'Você foi deslogado para iniciar a recuperação de senha.')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        if not email:
            messages.error(request, 'Por favor, informe seu email.')
            return render(request, 'didacta/autenticacao/password_reset_request.html')

        try:
            user = User.objects.get(email__iexact=email)
            if not user.is_active:
                messages.error(request, 'Esta conta está inativa. Entre em contato com o suporte.')
                return render(request, 'didacta/autenticacao/password_reset_request.html')

            import random
            codigo = ''.join([str(random.randint(0, 9)) for _ in range(6)])

            EmailVerificationCode.objects.create(
                usuario=user,
                codigo=codigo
            )

            subject = 'Recuperação de Senha - Didacta Vision'
            body = (
                f'Olá {user.nome_completo},\n\nVocê solicitou a recuperação de senha.\n\n'
                f'Seu código de verificação é: {codigo}\n\n'
                'Este código é válido por 10 minutos.\n\n'
                'Se você não solicitou esta recuperação, ignore este email.'
            )
            recipient_list = [user.email]
            enviado, erro = send_verification_email(recipient_list, subject, body)

            if enviado:
                messages.success(
                    request,
                    f'Código de verificação enviado para {user.email}. '
                    'Se não receber em 2–3 minutos, confira a pasta de spam.'
                )
            else:
                msg = f'O e-mail pode não ter sido entregue. Use o código abaixo para continuar: {codigo}'
                if settings.DEBUG and erro:
                    msg += f' (Detalhe: {erro})'
                messages.warning(request, msg)

            request.session['password_reset_user_id'] = user.id
            return redirect('didacta:password_reset_verify')
        except User.DoesNotExist:
            messages.error(request, 'Email não encontrado em nosso sistema.')

    return render(request, 'didacta/autenticacao/password_reset_request.html')

def password_reset_verify(request):
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, 'Você foi deslogado para continuar a recuperação de senha.')

    user_id = request.session.get('password_reset_user_id')

    if not user_id:
        messages.error(request, 'Sessão expirada. Por favor, solicite a recuperação novamente.')
        return redirect('didacta:password_reset_request')

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Usuário não encontrado.')
        del request.session['password_reset_user_id']
        return redirect('didacta:password_reset_request')

    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()

        if not codigo:
            messages.error(request, 'Por favor, informe o código de verificação.')
            return render(request, 'didacta/autenticacao/password_reset_verify.html', {'user': user})

        codigo_obj = EmailVerificationCode.objects.filter(
            usuario=user,
            codigo=codigo,
            usado=False
        ).order_by('-created_at').first()

        if codigo_obj and codigo_obj.is_valid():
            codigo_obj.usado = True
            codigo_obj.save()

            if request.user.is_authenticated:
                logout(request)
            
            request.session['password_reset_verified'] = True
            return redirect('didacta:password_reset_confirm')
        else:
            messages.error(request, 'Código inválido ou expirado. Por favor, tente novamente.')

    return render(request, 'didacta/autenticacao/password_reset_verify.html', {'user': user})

def password_reset_confirm(request):
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, 'Você foi deslogado para continuar a recuperação de senha.')

    user_id = request.session.get('password_reset_user_id')
    verified = request.session.get('password_reset_verified', False)

    if not user_id or not verified:
        messages.error(request, 'Sessão expirada. Por favor, solicite a recuperação novamente.')
        return redirect('didacta:password_reset_request')

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Usuário não encontrado.')
        del request.session['password_reset_user_id']
        del request.session['password_reset_verified']
        return redirect('didacta:password_reset_request')

    if request.method == 'POST':
        password1 = request.POST.get('password1', '').strip()
        password2 = request.POST.get('password2', '').strip()

        if not password1 or not password2:
            messages.error(request, 'Por favor, preencha todos os campos.')
            return render(request, 'didacta/autenticacao/password_reset_confirm.html', {'user': user})

        if password1 != password2:
            messages.error(request, 'As senhas não coincidem.')
            return render(request, 'didacta/autenticacao/password_reset_confirm.html', {'user': user})

        if len(password1) < 8:
            messages.error(request, 'A senha deve ter pelo menos 8 caracteres.')
            return render(request, 'didacta/autenticacao/password_reset_confirm.html', {'user': user})

        user.set_password(password1)
        user.save()

        del request.session['password_reset_user_id']
        del request.session['password_reset_verified']

        messages.success(request, 'Senha alterada com sucesso! Faça login com sua nova senha.')
        return redirect('didacta:login')

    return render(request, 'didacta/autenticacao/password_reset_confirm.html', {'user': user})

def index(request):
    filmes = Film.objects.filter(
        ativo=True,
        session_set__isnull=False
    ).distinct().order_by('-created_at')

    paginator = Paginator(filmes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'didacta/pagina_inicial.html', context)

@login_required
def profile_view(request):
    user = request.user
    form_password = PasswordChangeForm(user)

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            form = UserUpdateForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Perfil atualizado com sucesso!')
                return redirect('didacta:profile')
        elif 'change_password' in request.POST:
            form_password = PasswordChangeForm(user, request.POST)
            if form_password.is_valid():
                user.set_password(form_password.cleaned_data['nova_senha'])
                user.save()
                messages.success(request, 'Senha alterada com sucesso!')
                return redirect('didacta:profile')
            form = UserUpdateForm(instance=user)
        else:
            form = UserUpdateForm(instance=user)
    else:
        form = UserUpdateForm(instance=user)

    reservas = Reservation.objects.filter(usuario=user).select_related('usuario', 'sessao', 'sessao__filme').order_by('-created_at')[:10]

    context = {
        'user': user,
        'form': form,
        'form_password': form_password,
        'reservas': reservas,
    }
    return render(request, 'didacta/perfil_usuario.html', context)

@login_required
def delete_account_view(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Sua conta foi excluída com sucesso.')
        return redirect('didacta:index')

    return render(request, 'didacta/excluir_conta.html')

def film_detail(request, pk):
    filme = get_object_or_404(Film, pk=pk, ativo=True)
    sessoes_futuras = filme.session_set.filter(
        ativo=True
    ).order_by('data_hora')

    reservas_por_sessao = {}
    if request.user.is_authenticated:
        reservas = Reservation.objects.filter(
            usuario=request.user,
            sessao__in=sessoes_futuras,
            status__in=['reservado', 'presente']
        ).select_related('sessao')
        for reserva in reservas:
            reservas_por_sessao[reserva.sessao_id] = reserva

    comentarios = filme.forumcomment_set.filter(ativo=True, parent=None).order_by('-created_at')

    pode_comentar = False
    if request.user.is_authenticated:
        comment = ForumComment(filme=filme, usuario=request.user)
        pode_comentar = comment.pode_comentar(request.user)

    context = {
        'filme': filme,
        'sessoes_futuras': sessoes_futuras,
        'reservas_por_sessao': reservas_por_sessao,
        'comentarios': comentarios,
        'pode_comentar': pode_comentar,
    }
    return render(request, 'didacta/filmes/detalhes_filme.html', context)

class FilmCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Film
    form_class = FilmForm
    template_name = 'didacta/filmes/formulario_filme.html'
    success_url = reverse_lazy('didacta:film_list_admin')

    def test_func(self):
        return self.request.user.is_admin_or_professor()

    def form_valid(self, form):
        filme = form.save()
        usuarios = User.objects.filter(is_active=True)
        notificacoes = []
        for usuario in usuarios:
            notificacoes.append(
                Notification(
                    usuario=usuario,
                    titulo='Novo Filme Cadastrado',
                    mensagem=f'O filme "{filme.titulo}" foi adicionado ao catálogo. Confira as sessões disponíveis!',
                    tipo='filme_criado'
                )
            )
        if notificacoes:
            Notification.objects.bulk_create(notificacoes)
        messages.success(self.request, 'Filme criado com sucesso!')
        return super().form_valid(form)

class FilmUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Film
    form_class = FilmForm
    template_name = 'didacta/filmes/formulario_filme.html'
    success_url = reverse_lazy('didacta:film_list_admin')

    def test_func(self):
        return self.request.user.is_admin_or_professor()

    def form_valid(self, form):
        filme = form.save()
        usuarios = User.objects.filter(is_active=True)
        notificacoes = []
        for usuario in usuarios:
            notificacoes.append(
                Notification(
                    usuario=usuario,
                    titulo='Filme Atualizado',
                    mensagem=f'O filme "{filme.titulo}" teve suas informações atualizadas. Confira as novidades!',
                    tipo='filme_atualizado'
                )
            )
        if notificacoes:
            Notification.objects.bulk_create(notificacoes)
        messages.success(self.request, 'Filme atualizado com sucesso!')
        return super().form_valid(form)

class FilmDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Film
    template_name = 'didacta/filmes/confirmar_exclusao_filme.html'
    success_url = reverse_lazy('didacta:film_list_admin')

    def test_func(self):
        return self.request.user.is_admin_or_professor()

    def delete(self, request, *args, **kwargs):
        filme = self.get_object()
        if not filme.pode_ser_deletado():
            messages.error(request, 'Não é possível deletar este filme. Ele possui sessões futuras ou comentários ativos.')
            return redirect('didacta:film_list_admin')
        
        titulo_filme = filme.titulo
        filme_id = filme.pk
        
        usuarios = User.objects.filter(is_active=True)
        notificacoes = []
        for usuario in usuarios:
            notificacoes.append(
                Notification(
                    usuario=usuario,
                    titulo='Filme Removido',
                    mensagem=f'O filme "{titulo_filme}" foi removido do catálogo.',
                    tipo='filme_removido'
                )
            )
        
        for notif in notificacoes:
            notif.save()
        
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Filme deletado com sucesso!')
        return response

@login_required
def film_list_admin(request):
    if not request.user.is_admin_or_professor():
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('didacta:index')

    filmes = Film.objects.all().order_by('-created_at')
    paginator = Paginator(filmes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'didacta/filmes/lista_admin_filmes.html', {'page_obj': page_obj})

class SessionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Session
    form_class = SessionForm
    template_name = 'didacta/sessoes/formulario_sessao.html'
    success_url = reverse_lazy('didacta:session_list_admin')

    def test_func(self):
        return self.request.user.is_admin_or_professor()

    def form_valid(self, form):
        sessao = form.save()
        usuarios = User.objects.filter(is_active=True)
        notificacoes = []
        for usuario in usuarios:
            notificacoes.append(
                Notification(
                    usuario=usuario,
                    titulo='Nova Sessão Disponível',
                    mensagem=f'Nova sessão criada do filme "{sessao.filme.titulo}"! Disponível em {sessao.data_hora.strftime("%d/%m/%Y às %H:%M")}',
                    tipo='sessao_criada'
                )
            )
        if notificacoes:
            Notification.objects.bulk_create(notificacoes)
        messages.success(self.request, 'Sessão criada com sucesso!')
        return super().form_valid(form)

class SessionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Session
    form_class = SessionForm
    template_name = 'didacta/sessoes/formulario_sessao.html'
    success_url = reverse_lazy('didacta:session_list_admin')

    def test_func(self):
        return self.request.user.is_admin_or_professor()

    def form_valid(self, form):
        sessao = form.save()
        usuarios = User.objects.filter(is_active=True)
        notificacoes = []
        for usuario in usuarios:
            notificacoes.append(
                Notification(
                    usuario=usuario,
                    titulo='Sessão Atualizada',
                    mensagem=f'A sessão do filme "{sessao.filme.titulo}" foi atualizada. Confira as novas informações!',
                    tipo='sessao_atualizada'
                )
            )
        if notificacoes:
            Notification.objects.bulk_create(notificacoes)
        
        if sessao.pk:
            reservas = Reservation.objects.filter(
                sessao=sessao,
                status__in=['reservado', 'presente']
            ).select_related('usuario', 'sessao', 'sessao__filme')
            notificacoes_reservas = []
            for reserva in reservas:
                if reserva.usuario:
                    notificacoes_reservas.append(
                        Notification(
                            usuario=reserva.usuario,
                            titulo='Sessão Alterada - Sua Reserva',
                            mensagem=f'A sessão do filme {sessao.filme.titulo} em que você tem reserva foi alterada. Verifique os novos detalhes!',
                            tipo='sessao_alterada'
                        )
                    )
            if notificacoes_reservas:
                Notification.objects.bulk_create(notificacoes_reservas)

        messages.success(self.request, 'Sessão atualizada com sucesso!')
        return super().form_valid(form)

class SessionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Session
    template_name = 'didacta/sessoes/confirmar_exclusao_sessao.html'
    success_url = reverse_lazy('didacta:session_list_admin')

    def test_func(self):
        return self.request.user.is_admin_or_professor()

    def delete(self, request, *args, **kwargs):
        sessao = self.get_object()
        
        titulo_filme = sessao.filme.titulo
        data_hora = sessao.data_hora.strftime("%d/%m/%Y às %H:%M")
        sessao_id = sessao.pk
        
        usuarios = User.objects.filter(is_active=True)
        notificacoes = []
        for usuario in usuarios:
            notificacoes.append(
                Notification(
                    usuario=usuario,
                    titulo='Sessão Cancelada',
                    mensagem=f'A sessão do filme "{titulo_filme}" agendada para {data_hora} foi cancelada.',
                    tipo='sessao_cancelada'
                )
            )
        
        reservas = Reservation.objects.filter(
            sessao_id=sessao_id,
            status__in=['reservado', 'presente']
        ).select_related('usuario', 'sessao', 'sessao__filme')
        notificacoes_reservas = []
        for reserva in reservas:
            if reserva.usuario:
                notificacoes_reservas.append(
                    Notification(
                        usuario=reserva.usuario,
                        titulo='Sessão Cancelada - Sua Reserva',
                        mensagem=f'A sessão do filme {titulo_filme} em que você tinha reserva foi cancelada. Sua reserva foi automaticamente cancelada.',
                        tipo='sessao_cancelada'
                    )
                )
        
        for notif in notificacoes:
            notif.save()
        for notif in notificacoes_reservas:
            notif.save()

        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Sessão deletada com sucesso!')
        return response

@login_required
def session_list_admin(request):
    if not request.user.is_admin_or_professor():
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('didacta:index')

    sessoes = Session.objects.all().order_by('-data_hora')
    paginator = Paginator(sessoes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'didacta/sessoes/lista_admin_sessoes.html', {'page_obj': page_obj})

def session_detail(request, pk):
    sessao = get_object_or_404(Session.objects.select_related('filme'), pk=pk, ativo=True)

    reserva_usuario = None
    if request.user.is_authenticated:
        reserva_usuario = Reservation.objects.filter(
            usuario=request.user,
            sessao=sessao,
            status__in=['reservado', 'presente']
        ).first()

    context = {
        'sessao': sessao,
        'reserva_usuario': reserva_usuario,
    }
    return render(request, 'didacta/sessoes/detalhes_sessao.html', context)

@login_required
def session_detail_admin(request, pk):
    if not request.user.is_admin_or_professor():
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('didacta:index')

    sessao = get_object_or_404(Session, pk=pk)
    reservas = Reservation.objects.filter(sessao=sessao).select_related('usuario').order_by('-status', 'usuario__nome_completo')

    context = {
        'sessao': sessao,
        'reservas': reservas,
    }
    return render(request, 'didacta/sessoes/detalhes_admin_sessao.html', context)

@login_required
def reservation_create(request, session_id):
    sessao = get_object_or_404(Session.objects.select_related('filme'), pk=session_id, ativo=True)

    if request.method == 'POST':
        form = ReservationForm(request.POST, user=request.user)
        form.fields['sessao'].initial = sessao
        if form.is_valid():
            try:
                reserva = Reservation.objects.create(
                    usuario=request.user,
                    sessao=sessao,
                    status='reservado'
                )

                Notification.objects.create(
                    usuario=request.user,
                    titulo='Reserva Confirmada',
                    mensagem=f'Sua reserva para a sessão de {sessao.filme.titulo} foi confirmada.',
                    tipo='reserva_criada'
                )

                messages.success(request, 'Reserva realizada com sucesso!')
                return redirect('didacta:reservation_list')
            except (ValidationError, IntegrityError) as e:
                if isinstance(e, ValidationError) and hasattr(e, 'error_dict'):
                    for field, errors in e.error_dict.items():
                        for error in errors:
                            form.add_error(field, error)
                else:
                    form.add_error(None, 'Você já possui uma reserva ativa para esta sessão ou não há vagas disponíveis.')
                    messages.error(request, 'Não foi possível criar a reserva. Verifique se há vagas e se você já não possui uma reserva.')
    else:
        form = ReservationForm(user=request.user, initial={'sessao': sessao})
        form.fields['sessao'].initial = sessao

    context = {
        'form': form,
        'sessao': sessao,
    }
    return render(request, 'didacta/reservas/criar_reserva.html', context)

@login_required
def reservation_list(request):
    reservas = Reservation.objects.filter(
        usuario=request.user
    ).exclude(status='cancelado').select_related('usuario', 'sessao', 'sessao__filme').order_by('-created_at')

    reservas_futuras = reservas.filter(sessao__data_hora__gt=timezone.now())
    reservas_passadas = reservas.filter(sessao__data_hora__lte=timezone.now())

    context = {
        'reservas_futuras': reservas_futuras,
        'reservas_passadas': reservas_passadas,
    }
    return render(request, 'didacta/reservas/lista_reservas.html', context)

@login_required
def reservation_cancel(request, pk):
    reserva = get_object_or_404(Reservation.objects.select_related('usuario', 'sessao', 'sessao__filme'), pk=pk, usuario=request.user)

    if reserva.status not in ['reservado', 'presente']:
        messages.error(request, 'Esta reserva não pode ser cancelada.')
        return redirect('didacta:reservation_list')

    if request.method == 'POST':
        form = ReservationCancelForm(request.POST)
        if form.is_valid():
            reserva.status = 'cancelado'
            reserva.justificativa_cancelamento = form.cleaned_data.get('justificativa', '')
            reserva.save()

            Notification.objects.create(
                usuario=request.user,
                titulo='Reserva Cancelada',
                mensagem=f'Sua reserva para a sessão de {reserva.sessao.filme.titulo} foi cancelada.',
                tipo='reserva_cancelada'
            )

            messages.success(request, 'Reserva cancelada com sucesso!')
            return redirect('didacta:reservation_list')
    else:
        form = ReservationCancelForm()

    return render(request, 'didacta/reservas/confirmar_cancelamento_reserva.html', {'reserva': reserva, 'form': form})

@login_required
def mark_presence(request, reservation_id):
    if not request.user.is_admin_or_professor():
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('didacta:index')

    reserva = get_object_or_404(Reservation.objects.select_related('usuario', 'sessao', 'sessao__filme'), pk=reservation_id)

    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['reservado', 'presente', 'falta', 'falta_justificada']:
            reserva.status = status
            reserva.save()

            if reserva.usuario:
                Notification.objects.create(
                    usuario=reserva.usuario,
                    titulo='Presença Registrada',
                    mensagem=f'Sua presença na sessão de {reserva.sessao.filme.titulo} foi registrada como: {reserva.get_status_display()}.',
                    tipo='reserva_confirmada'
                )

            messages.success(request, f'Status atualizado para: {reserva.get_status_display()}')
            return redirect('didacta:session_detail_admin', pk=reserva.sessao.pk)

    return redirect('didacta:session_detail_admin', pk=reserva.sessao.pk)

@login_required
def forum_comment_create(request, film_id):
    filme = get_object_or_404(Film, pk=film_id, ativo=True)

    comment = ForumComment(filme=filme, usuario=request.user)
    if not comment.pode_comentar(request.user):
        messages.error(
            request,
            'Você precisa ter presença confirmada ou falta justificada em uma sessão deste filme para comentar.'
        )
        return redirect('didacta:film_detail', pk=film_id)

    if request.method == 'POST':
        form = ForumCommentForm(request.POST, user=request.user, filme=filme)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.filme = filme
            comentario.usuario = request.user
            comentario.save()
            messages.success(request, 'Comentário publicado com sucesso!')
            return redirect('didacta:film_detail', pk=film_id)
    else:
        parent_id = request.GET.get('parent')
        form = ForumCommentForm(user=request.user, filme=filme)
        if parent_id:
            try:
                parent = ForumComment.objects.get(pk=parent_id, filme=filme)
                form.fields['parent'].initial = parent
            except ForumComment.DoesNotExist:
                pass

    context = {
        'form': form,
        'filme': filme,
    }
    return render(request, 'didacta/forum/formulario_comentario.html', context)

@login_required
def forum_comment_delete(request, pk):
    comentario = get_object_or_404(ForumComment, pk=pk)

    if not (request.user.is_admin_or_professor() or comentario.usuario == request.user):
        messages.error(request, 'Você não tem permissão para deletar este comentário.')
        return redirect('didacta:film_detail', pk=comentario.filme.pk)

    if request.method == 'POST':
        filme_id = comentario.filme.pk
        comentario.ativo = False
        comentario.save()
        messages.success(request, 'Comentário removido com sucesso!')
        return redirect('didacta:film_detail', pk=filme_id)

    return render(request, 'didacta/forum/confirmar_exclusao_comentario.html', {'comentario': comentario})

def help_ticket_create(request):
    if request.user.is_authenticated and request.user.is_admin_or_professor():
        messages.error(request, 'Administradores não podem criar solicitações de suporte.')
        return redirect('didacta:help_ticket_list')
    
    if request.method == 'POST':
        form = HelpTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            if request.user.is_authenticated:
                ticket.usuario = request.user
            ticket.save()
            messages.success(request, 'Ticket de suporte criado com sucesso!')
            return redirect('didacta:index')
    else:
        form = HelpTicketForm()

    return render(request, 'didacta/suporte/criar_ticket_suporte.html', {'form': form})

@login_required
def help_ticket_list(request):
    if request.user.is_admin_or_professor():
        tickets = HelpTicket.objects.all().order_by('-created_at')
    else:
        tickets = HelpTicket.objects.filter(usuario=request.user).order_by('-created_at')

    paginator = Paginator(tickets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'didacta/suporte/lista_tickets_suporte.html', {'page_obj': page_obj})

@login_required
def help_ticket_detail(request, pk):
    ticket = get_object_or_404(HelpTicket, pk=pk)

    if not (request.user.is_admin_or_professor() or ticket.usuario == request.user):
        messages.error(request, 'Você não tem permissão para acessar este ticket.')
        return redirect('didacta:help_ticket_list')

    if request.method == 'POST' and request.user.is_admin_or_professor():
        resposta = request.POST.get('resposta')
        status = request.POST.get('status')
        status_anterior = ticket.status
        tinha_resposta_antes = bool(ticket.resposta)
        
        if resposta:
            ticket.resposta = resposta
        if status:
            ticket.status = status
        
        if resposta and not tinha_resposta_antes and ticket.status == 'aberto':
            ticket.status = 'respondido'
        
        ticket.save()
        
        if ticket.usuario and resposta and (not tinha_resposta_antes or status_anterior == 'aberto'):
            Notification.objects.create(
                usuario=ticket.usuario,
                titulo='Ticket de Suporte Respondido',
                mensagem=f'Seu ticket "{ticket.assunto}" foi respondido. Verifique a resposta em Suporte.',
                tipo='suporte_respondido'
            )
        
        messages.success(request, 'Ticket atualizado com sucesso!')
        return redirect('didacta:help_ticket_detail', pk=pk)

    return render(request, 'didacta/suporte/detalhes_ticket_suporte.html', {'ticket': ticket})

@login_required
def notification_list(request):
    if request.user.is_admin_or_professor():
        notificacoes = Notification.objects.filter(usuario=request.user, lida=False).order_by('-created_at')
    else:
        tipos_permitidos = [
            'reserva_criada', 'reserva_cancelada', 'reserva_confirmada',
            'sessao_alterada', 'sessao_cancelada', 'sessao_reagendada',
            'sessao_criada', 'sessao_atualizada', 'sessao_cancelada',
            'suporte_respondido'
        ]
        notificacoes = Notification.objects.filter(
            usuario=request.user,
            lida=False,
            tipo__in=tipos_permitidos
        ).order_by('-created_at')

    paginator = Paginator(notificacoes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'didacta/notificacoes/lista_notificacoes.html', {'page_obj': page_obj})

@login_required
def notification_mark_read(request, pk):
    notificacao = get_object_or_404(Notification, pk=pk, usuario=request.user)
    notificacao.lida = True
    notificacao.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    messages.success(request, 'Notificação marcada como lida.')
    return redirect('didacta:notification_list')

@login_required
def notification_mark_all_read(request):
    Notification.objects.filter(usuario=request.user, lida=False).update(lida=True)
    messages.success(request, 'Todas as notificações foram marcadas como lidas.')
    return redirect('didacta:notification_list')
