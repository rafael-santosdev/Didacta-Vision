from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta

from .models import Film, Session, Reservation, ForumComment, Notification, HelpTicket

User = get_user_model()

class UserModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            nome_completo='Test User',
            tipo_usuario='aluno'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.nome_completo, 'Test User')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_email_unique(self):
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='testuser2',
                email='test@example.com',
                password='testpass123',
                nome_completo='Test User 2'
            )

    def test_is_admin_or_professor(self):
        self.assertFalse(self.user.is_admin_or_professor())

        self.user.tipo_usuario = 'professor'
        self.user.save()
        self.assertTrue(self.user.is_admin_or_professor())

        self.user.tipo_usuario = 'admin'
        self.user.save()
        self.assertTrue(self.user.is_admin_or_professor())

class FilmModelTest(TestCase):

    def setUp(self):
        self.filme = Film.objects.create(
            titulo='Filme Teste',
            sinopse='Sinopse do filme teste',
            duracao=120,
            classificacao='12',
            genero='Ação',
            ativo=True
        )

    def test_film_creation(self):
        self.assertEqual(self.filme.titulo, 'Filme Teste')
        self.assertEqual(self.filme.duracao, 120)
        self.assertTrue(self.filme.ativo)

    def test_titulo_unique_when_active(self):
        with self.assertRaises(Exception):
            Film.objects.create(
                titulo='Filme Teste',
                sinopse='Outra sinopse',
                duracao=90,
                ativo=True
            )

    def test_trailer_url_unique(self):
        Film.objects.create(
            titulo='Outro Filme',
            sinopse='Sinopse',
            duracao=90,
            trailer_url='https://youtube.com/watch?v=123',
            ativo=True
        )

        with self.assertRaises(Exception):
            Film.objects.create(
                titulo='Terceiro Filme',
                sinopse='Sinopse',
                duracao=90,
                trailer_url='https://youtube.com/watch?v=123',
                ativo=True
            )

class ReservationTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            nome_completo='Test User'
        )

        self.filme = Film.objects.create(
            titulo='Filme Teste',
            sinopse='Sinopse',
            duracao=120,
            ativo=True
        )

        self.sessao = Session.objects.create(
            filme=self.filme,
            data_hora=timezone.now() + timedelta(days=1),
            capacidade_total=2,
            local='Sala 1',
            ativo=True
        )

    def test_reservation_respects_capacity(self):
        Reservation.objects.create(
            usuario=self.user,
            sessao=self.sessao,
            status='reservado'
        )

        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
            nome_completo='Test User 2'
        )
        Reservation.objects.create(
            usuario=user2,
            sessao=self.sessao,
            status='reservado'
        )

        self.assertEqual(self.sessao.vagas_disponiveis, 0)
        self.assertTrue(self.sessao.esta_cheia)

        user3 = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='testpass123',
            nome_completo='Test User 3'
        )
        reserva3 = Reservation(
            usuario=user3,
            sessao=self.sessao,
            status='reservado'
        )

        with self.assertRaises(Exception):
            reserva3.clean()
            reserva3.save()

    def test_reservation_unique_per_user_session(self):
        Reservation.objects.create(
            usuario=self.user,
            sessao=self.sessao,
            status='reservado'
        )

        with self.assertRaises(Exception):
            Reservation.objects.create(
                usuario=self.user,
                sessao=self.sessao,
                status='reservado'
            )

    def test_reservation_cancel_frees_capacity(self):
        reserva = Reservation.objects.create(
            usuario=self.user,
            sessao=self.sessao,
            status='reservado'
        )

        self.assertEqual(self.sessao.vagas_disponiveis, 1)

        reserva.status = 'cancelado'
        reserva.save()

        self.sessao.refresh_from_db()
        self.assertEqual(self.sessao.vagas_disponiveis, 2)

class ForumCommentTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            nome_completo='Test User'
        )

        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            nome_completo='Admin User',
            tipo_usuario='admin'
        )

        self.filme = Film.objects.create(
            titulo='Filme Teste',
            sinopse='Sinopse',
            duracao=120,
            ativo=True
        )

        self.sessao = Session.objects.create(
            filme=self.filme,
            data_hora=timezone.now() + timedelta(days=1),
            capacidade_total=50,
            local='Sala 1',
            ativo=True
        )

    def test_forum_comment_requires_presence(self):
        comment = ForumComment(filme=self.filme, usuario=self.user)

        self.assertFalse(comment.pode_comentar(self.user))

        Reservation.objects.create(
            usuario=self.user,
            sessao=self.sessao,
            status='presente'
        )

        self.assertTrue(comment.pode_comentar(self.user))

    def test_forum_comment_allows_justified_absence(self):
        Reservation.objects.create(
            usuario=self.user,
            sessao=self.sessao,
            status='falta_justificada'
        )

        comment = ForumComment(filme=self.filme, usuario=self.user)
        self.assertTrue(comment.pode_comentar(self.user))

    def test_admin_can_always_comment(self):
        comment = ForumComment(filme=self.filme, usuario=self.admin)
        self.assertTrue(comment.pode_comentar(self.admin))

    def test_forum_comment_text_length(self):
        comment = ForumComment(
            filme=self.filme,
            usuario=self.user,
            texto='Curto'
        )
        with self.assertRaises(Exception):
            comment.full_clean()

        comment.texto = 'A' * 501
        with self.assertRaises(Exception):
            comment.full_clean()

class AccountDeletionTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            nome_completo='Test User'
        )
        self.client = Client()

    def test_user_can_delete_own_account(self):
        self.client.login(email='test@example.com', password='testpass123')

        self.assertTrue(self.user.is_active)

        self.user.is_active = False
        self.user.save()

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_deleted_user_cannot_login(self):
        self.user.is_active = False
        self.user.save()

        response = self.client.post('/login/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })

        self.assertFalse(response.wsgi_request.user.is_authenticated)

class NotificationTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            nome_completo='Test User'
        )

    def test_notification_creation(self):
        notification = Notification.objects.create(
            usuario=self.user,
            titulo='Teste',
            mensagem='Mensagem de teste',
            tipo='outro'
        )

        self.assertEqual(notification.usuario, self.user)
        self.assertFalse(notification.lida)

    def test_notification_mark_as_read(self):
        notification = Notification.objects.create(
            usuario=self.user,
            titulo='Teste',
            mensagem='Mensagem de teste'
        )

        notification.lida = True
        notification.save()

        notification.refresh_from_db()
        self.assertTrue(notification.lida)

class HelpTicketTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            nome_completo='Test User'
        )

    def test_help_ticket_creation(self):
        ticket = HelpTicket.objects.create(
            usuario=self.user,
            assunto='Problema',
            mensagem='Descrição do problema',
            status='aberto'
        )

        self.assertEqual(ticket.usuario, self.user)
        self.assertEqual(ticket.status, 'aberto')

    def test_help_ticket_without_user(self):
        ticket = HelpTicket.objects.create(
            assunto='Problema',
            mensagem='Descrição do problema',
            status='aberto'
        )

        self.assertIsNone(ticket.usuario)

class AjaxInteractionsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='aluno',
            email='aluno@example.com',
            password='password123',
            nome_completo='Aluno Teste',
            tipo_usuario='aluno',
            email_verificado=True
        )
        self.admin = User.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='adminpass123',
            nome_completo='Admin Teste',
            is_admin=True
        )
        self.filme = Film.objects.create(
            titulo='Interstellar',
            sinopse='Viagem interestelar pela ciência.',
            duracao=169,
            classificacao='12',
            genero='Ficção Científica',
            tema='Astrofísica',
            trailer_url='https://www.youtube.com/watch?v=zSWdZVtXT7E',
            ativo=True
        )
        self.sessao = Session.objects.create(
            filme=self.filme,
            data_hora=timezone.now() + timedelta(days=2),
            capacidade_total=30,
            local='Auditório Central',
            ativo=True
        )

    def test_ajax_reservation_and_cancel(self):
        self.client.login(email='aluno@example.com', password='password123')
        # Criar reserva via AJAX
        res = self.client.post(
            reverse('didacta:reservation_create', args=[self.sessao.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertIn('reserva_id', data)
        reserva_id = data['reserva_id']

        # Cancelar reserva via AJAX
        res_cancel = self.client.post(
            reverse('didacta:reservation_cancel', args=[reserva_id]),
            {'justificativa': 'Imprevisto pessoal'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res_cancel.status_code, 200)
        data_cancel = res_cancel.json()
        self.assertTrue(data_cancel['success'])

        reserva = Reservation.objects.get(pk=reserva_id)
        self.assertEqual(reserva.status, 'cancelado')
        self.assertEqual(reserva.justificativa_cancelamento, 'Imprevisto pessoal')

    def test_ajax_mark_presence(self):
        reserva = Reservation.objects.create(
            usuario=self.user,
            sessao=self.sessao,
            status='reservado'
        )
        self.client.login(email='admin@example.com', password='adminpass123')
        res = self.client.post(
            reverse('didacta:mark_presence', args=[reserva.pk]),
            {'status': 'presente'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['new_status'], 'presente')

        reserva.refresh_from_db()
        self.assertEqual(reserva.status, 'presente')

    def test_ajax_notifications(self):
        notif = Notification.objects.create(
            usuario=self.user,
            titulo='Aviso de Sessão',
            mensagem='Sua sessão começa em breve.'
        )
        self.client.login(email='aluno@example.com', password='password123')

        res = self.client.post(
            reverse('didacta:notification_mark_read', args=[notif.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        notif.refresh_from_db()
        self.assertTrue(notif.lida)

        # Criar outra notificação e marcar todas
        Notification.objects.create(usuario=self.user, titulo='Outro aviso', mensagem='...')
        res_all = self.client.post(
            reverse('didacta:notification_mark_all_read'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res_all.status_code, 200)
        data_all = res_all.json()
        self.assertTrue(data_all['success'])
        self.assertEqual(data_all['unread_count'], 0)

    def test_catalog_search(self):
        # Acesso anônimo ou logado à página inicial
        res = self.client.get(reverse('didacta:index'), {'q': 'Interstellar'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Interstellar')



