from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import JsonResponse
from django.core.mail import send_mail
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

def register_view(request):
    if request.user.is_authenticated:
        return redirect('didacta:index')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            import random
            codigo = ''.join([str(random.randint(0, 9)) for _ in range(6)])

            EmailVerificationCode.objects.create(
                usuario=user,
                codigo=codigo
            )

            try:
                send_mail(
                    subject='Código de Verificação - Didacta Vision',
                    message=f'Olá {user.nome_completo},\n\nBem-vindo ao Didacta Vision!\n\nSeu código de verificação é: {codigo}\n\nEste código é válido por 10 minutos.\n\nUse este código para verificar sua conta e fazer login.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                messages.success(request, f'Conta criada com sucesso! Código de verificação enviado para {user.email}')
                request.session['verification_user_id'] = user.id
                return redirect('didacta:verify_code')
            except Exception as e:
                messages.error(request, f'Conta criada, mas erro ao enviar código de verificação: {str(e)}. Entre em contato com o suporte.')
                return redirect('didacta:login')
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

        from django.contrib.auth import authenticate
        user = authenticate(request, username=nome_ou_email, password=password)

        if user is not None:
            if user.is_active:
                login(request, user, backend='didacta.autenticacao_backend.NomeOrEmailBackend')
                messages.success(request, f'Bem-vindo, {user.nome_completo}!')
                next_url = request.GET.get('next')
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                return redirect('didacta:index')
            else:
                messages.error(request, 'Conta inativa.')
        else:
            messages.error(request, 'Nome/email ou senha incorretos.')

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

    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()

        if not codigo:
            messages.error(request, 'Por favor, informe o código de verificação.')
            return render(request, 'didacta/autenticacao/verify_code.html', {'user': user})

        codigo_obj = EmailVerificationCode.objects.filter(
            usuario=user,
            codigo=codigo,
            usado=False
        ).order_by('-created_at').first()

        if codigo_obj and codigo_obj.is_valid():
            codigo_obj.usado = True
            codigo_obj.save()

            login(request, user, backend='didacta.autenticacao_backend.NomeOrEmailBackend')

            del request.session['verification_user_id']

            messages.success(request, f'Bem-vindo, {user.nome_completo}!')
            next_url = request.GET.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('didacta:index')
        else:
            messages.error(request, 'Código inválido ou expirado. Por favor, tente novamente.')

    return render(request, 'didacta/autenticacao/verify_code.html', {'user': user})

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'Você foi desconectado com sucesso.')
    return redirect('didacta:index')

def password_reset_request(request):
    if request.user.is_authenticated:
        return redirect('didacta:index')

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

            try:
                send_mail(
                    subject='Recuperação de Senha - Didacta Vision',
                    message=f'Olá {user.nome_completo},\n\nVocê solicitou a recuperação de senha.\n\nSeu código de verificação é: {codigo}\n\nEste código é válido por 10 minutos.\n\nSe você não solicitou esta recuperação, ignore este email.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                messages.success(request, f'Código de verificação enviado para {user.email}')
                request.session['password_reset_user_id'] = user.id
                return redirect('didacta:password_reset_verify')
            except Exception as e:
                messages.error(request, f'Erro ao enviar código de verificação: {str(e)}')
        except User.DoesNotExist:
            messages.error(request, 'Email não encontrado em nosso sistema.')

    return render(request, 'didacta/autenticacao/password_reset_request.html')

def password_reset_verify(request):
    if request.user.is_authenticated:
        return redirect('didacta:index')

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

            request.session['password_reset_verified'] = True
            return redirect('didacta:password_reset_confirm')
        else:
            messages.error(request, 'Código inválido ou expirado. Por favor, tente novamente.')

    return render(request, 'didacta/autenticacao/password_reset_verify.html', {'user': user})

def password_reset_confirm(request):
    if request.user.is_authenticated:
        return redirect('didacta:index')

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
    filmes = Film.objects.filter(ativo=True).order_by('-created_at')

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
    else:
        form = UserUpdateForm(instance=user)
        form_password = PasswordChangeForm(user)

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
        user.is_active = False
        user.save()
        logout(request)
        messages.success(request, 'Sua conta foi desativada com sucesso.')
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
        messages.success(request, 'Filme deletado com sucesso!')
        return super().delete(request, *args, **kwargs)

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
        sessao = form.instance
        if sessao.pk:
            reservas = Reservation.objects.filter(
                sessao=sessao,
                status__in=['reservado', 'presente']
            ).select_related('usuario', 'sessao', 'sessao__filme')
            for reserva in reservas:
                if reserva.usuario:
                    Notification.objects.create(
                        usuario=reserva.usuario,
                        titulo='Sessão Alterada',
                        mensagem=f'A sessão do filme {sessao.filme.titulo} foi alterada.',
                        tipo='sessao_alterada'
                    )

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
        reservas = Reservation.objects.filter(
            sessao=sessao,
            status__in=['reservado', 'presente']
        ).select_related('usuario', 'sessao', 'sessao__filme')
        for reserva in reservas:
            if reserva.usuario:
                Notification.objects.create(
                    usuario=reserva.usuario,
                    titulo='Sessão Cancelada',
                    mensagem=f'A sessão do filme {sessao.filme.titulo} foi cancelada.',
                    tipo='sessao_cancelada'
                )

        messages.success(request, 'Sessão deletada com sucesso!')
        return super().delete(request, *args, **kwargs)

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
    reservas = Reservation.objects.filter(sessao=sessao).select_related('usuario').order_by('usuario__nome_completo')

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
        if status in ['presente', 'falta', 'falta_justificada']:
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
        if resposta:
            ticket.resposta = resposta
        if status:
            ticket.status = status
        ticket.save()
        messages.success(request, 'Ticket atualizado com sucesso!')
        return redirect('didacta:help_ticket_detail', pk=pk)

    return render(request, 'didacta/suporte/detalhes_ticket_suporte.html', {'ticket': ticket})

@login_required
def notification_list(request):
    notificacoes = Notification.objects.filter(usuario=request.user).order_by('-created_at')

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

    return redirect('didacta:notification_list')

@login_required
def notification_mark_all_read(request):
    Notification.objects.filter(usuario=request.user, lida=False).update(lida=True)
    messages.success(request, 'Todas as notificações foram marcadas como lidas.')
    return redirect('didacta:notification_list')

