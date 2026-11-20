from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from didacta.models import User, Film, Session, Reservation, ForumComment, Notification


class Command(BaseCommand):
    help = 'Popula o banco de dados com dados realistas do projeto Luz, Ciência e Ação (IFRN) para apresentações e testes.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando o povoamento com dados de demonstração...'))

        # 1. Garantir que os usuários existentes estão com email verificado
        users_existentes = User.objects.all()
        for u in users_existentes:
            if not u.email_verificado:
                u.email_verificado = True
                u.save(update_fields=['email_verificado'])
                self.stdout.write(self.style.SUCCESS(f'Email verificado ativado para usuário existente: {u.email}'))

        # 2. Criar ou obter usuários de demonstração
        demo_password = 'Didacta@2026'

        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user, _ = User.objects.get_or_create(
                username='admin@ifrn.edu.br',
                defaults={
                    'email': 'admin@ifrn.edu.br',
                    'nome_completo': 'Administrador IFRN',
                    'first_name': 'Administrador',
                    'last_name': 'IFRN',
                    'tipo_usuario': 'admin',
                    'is_staff': True,
                    'is_superuser': True,
                    'is_admin': True,
                    'email_verificado': True,
                }
            )
            admin_user.set_password(demo_password)
            admin_user.save()

        prof_user, _ = User.objects.get_or_create(
            username='professor@ifrn.edu.br',
            defaults={
                'email': 'professor@ifrn.edu.br',
                'nome_completo': 'Prof. Carlos Menezes',
                'first_name': 'Prof. Carlos',
                'last_name': 'Menezes',
                'tipo_usuario': 'professor',
                'is_staff': True,
                'email_verificado': True,
            }
        )
        if not prof_user.nome_completo:
            prof_user.nome_completo = 'Prof. Carlos Menezes'
        if not prof_user.has_usable_password():
            prof_user.set_password(demo_password)
        prof_user.save()

        aluno1, _ = User.objects.get_or_create(
            username='mariasilva@ifrn.edu.br',
            defaults={
                'email': 'mariasilva@ifrn.edu.br',
                'nome_completo': 'Maria Silva',
                'first_name': 'Maria',
                'last_name': 'Silva',
                'tipo_usuario': 'aluno',
                'email_verificado': True,
            }
        )
        if not aluno1.nome_completo:
            aluno1.nome_completo = 'Maria Silva'
        if not aluno1.has_usable_password():
            aluno1.set_password(demo_password)
        aluno1.save()

        aluno2, _ = User.objects.get_or_create(
            username='joaopedro@ifrn.edu.br',
            defaults={
                'email': 'joaopedro@ifrn.edu.br',
                'nome_completo': 'João Pedro Albuquerque',
                'first_name': 'João Pedro',
                'last_name': 'Albuquerque',
                'tipo_usuario': 'aluno',
                'email_verificado': True,
            }
        )
        if not aluno2.nome_completo:
            aluno2.nome_completo = 'João Pedro Albuquerque'
        if not aluno2.has_usable_password():
            aluno2.set_password(demo_password)
        aluno2.save()

        # Aluno Danilo (se existir)
        danilo_user = User.objects.filter(email='danilolima28608@gmail.com').first()
        if danilo_user:
            danilo_user.email_verificado = True
            danilo_user.save()

        # 3. Ajustar filme teste pré-existente se houver
        filme_antigo = Film.objects.filter(titulo__icontains='Vingadores').first()
        if filme_antigo:
            filme_antigo.titulo = 'Vingadores: Ultimato (Edição Especial)'
            filme_antigo.tema = 'Cultura Pop e Ficção'
            filme_antigo.genero = 'Ação / Ficção Científica'
            filme_antigo.save()
            for s in filme_antigo.session_set.filter(local='wqsw'):
                s.local = 'Auditório Central - IFRN'
                s.save()

        # 4. Criar catálogo de filmes educativos
        filmes_dados = [
            {
                'titulo': 'O Menino que Descobriu o Vento',
                'sinopse': 'Contra todas as probabilidades, William Kamkwamba, um garoto de 13 anos em Malawi, inspira-se em um livro didático de ciências da biblioteca e inventa uma turbina eólica inovadora para salvar sua família e vila da seca severa e da fome.',
                'duracao': 113,
                'classificacao': '12',
                'genero': 'Drama / Biografia',
                'tema': 'Ciência e Sustentabilidade',
                'trailer_url': 'https://www.youtube.com/watch?v=nP_70h822v0',
                'cartaz_url': 'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=600&q=80',
            },
            {
                'titulo': 'Estrelas Além do Tempo',
                'sinopse': 'No auge da corrida espacial durante a Guerra Fria, uma equipe extraordinária de matemáticas e cientistas afro-americanas da NASA enfrenta o preconceito e desempenha um papel determinante no cálculo das trajetórias que levaram a humanidade ao espaço.',
                'duracao': 127,
                'classificacao': 'L',
                'genero': 'Biografia / História',
                'tema': 'Mulheres na Ciência',
                'trailer_url': 'https://www.youtube.com/watch?v=5wfrDhgUMGI',
                'cartaz_url': 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=600&q=80',
            },
            {
                'titulo': 'O Jogo da Imitação',
                'sinopse': 'Durante os dias mais sombrios da Segunda Guerra Mundial, o matemático britânico Alan Turing lidera um grupo confidencial de criptoanalistas em Bletchley Park para quebrar o aparentemente impenetrável código naval Enigma, dando origem aos primeiros computadores modernos.',
                'duracao': 114,
                'classificacao': '12',
                'genero': 'Biografia / Suspense',
                'tema': 'Computação e Criptografia',
                'trailer_url': 'https://www.youtube.com/watch?v=Ymk_A3n22Lg',
                'cartaz_url': 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=600&q=80',
            },
            {
                'titulo': 'Interestelar',
                'sinopse': 'Em um futuro onde as reservas naturais da Terra estão se esgotando, um grupo de exploradores e físicos recebe a missão mais urgente da humanidade: atravessar um recém-descoberto buraco de minhoca e encontrar um novo planeta habitável entre as galáxias.',
                'duracao': 169,
                'classificacao': '10',
                'genero': 'Ficção Científica',
                'tema': 'Astrofísica e Exploração',
                'trailer_url': 'https://www.youtube.com/watch?v=zSWdZVtXT7E',
                'cartaz_url': 'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=600&q=80',
            },
            {
                'titulo': 'Ilha das Flores',
                'sinopse': 'Um aclamado e contundente documentário em curta-metragem dirigido por Jorge Furtado que traça a trajetória de um tomate, do cultivo ao lixão da Ilha das Flores em Porto Alegre, confrontando com ironia e lucidez os absurdos do consumo desenfreado e da desigualdade humana.',
                'duracao': 13,
                'classificacao': 'L',
                'genero': 'Documentário',
                'tema': 'Cidadania e Economia',
                'trailer_url': 'https://www.youtube.com/watch?v=8mQzK5lUswQ',
                'cartaz_url': 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&w=600&q=80',
            },
            {
                'titulo': 'Que Horas Ela Volta?',
                'sinopse': 'A pernambucana Val trabalha há mais de uma década como empregada doméstica e babá em São Paulo. O equilíbrio da mansão se altera drasticamente quando sua filha Jéssica chega à capital para prestar vestibular de Arquitetura na USP, questionando os papéis sociais com firmeza e inteligência.',
                'duracao': 112,
                'classificacao': '12',
                'genero': 'Drama Nacional',
                'tema': 'Educação e Sociedade',
                'trailer_url': 'https://www.youtube.com/watch?v=j3oE5s3l2vE',
                'cartaz_url': 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=600&q=80',
            },
        ]

        filmes_criados = []
        for dado in filmes_dados:
            filme, criado = Film.objects.get_or_create(
                titulo=dado['titulo'],
                defaults=dado
            )
            if not criado:
                for k, v in dado.items():
                    setattr(filme, k, v)
                filme.save()
            filmes_criados.append(filme)
            self.stdout.write(self.style.SUCCESS(f'Filme carregado: "{filme.titulo}" ({filme.tema})'))

        # 5. Criar sessões (futuras e passadas para histórico e frequência)
        agora = timezone.now()

        # Evita acumular sessões duplicadas em execuções repetidas do seed.
        for filme in filmes_criados:
            sessoes_anteriores = list(filme.session_set.filter(ativo=True).order_by('data_hora', 'pk'))
            mantidas = []
            for sessao in sessoes_anteriores:
                duplicada = any(
                    sessao.local == anterior.local
                    and sessao.capacidade_total == anterior.capacidade_total
                    and abs((sessao.data_hora - anterior.data_hora).total_seconds()) < 24 * 60 * 60
                    for anterior in mantidas
                )
                if duplicada:
                    for reserva in sessao.reservation_set.all():
                        anterior = next(
                            anterior for anterior in mantidas
                            if anterior.local == sessao.local
                            and anterior.capacidade_total == sessao.capacidade_total
                            and abs((sessao.data_hora - anterior.data_hora).total_seconds()) < 24 * 60 * 60
                        )
                        reserva_existente = anterior.reservation_set.filter(usuario=reserva.usuario).exists()
                        if reserva_existente:
                            reserva.delete()
                        else:
                            reserva.sessao = anterior
                            reserva.save(update_fields=['sessao'])
                    sessao.delete()
                else:
                    mantidas.append(sessao)

        locais = [
            'Auditório Central - IFRN Campus Natal',
            'Miniauditório Bloco B - IFRN',
            'Sala Multimídia de Projeção - IFRN'
        ]

        # Sessões Futuras
        sessoes_futuras = []
        horarios = [
            agora + timedelta(days=2, hours=3),
            agora + timedelta(days=5, hours=5),
            agora + timedelta(days=7, hours=2),
            agora + timedelta(days=10, hours=4),
        ]

        for i, filme in enumerate(filmes_criados[:4]):
            data_sessao = horarios[i % len(horarios)]
            local_sessao = locais[i % len(locais)]
            sessao, _ = Session.objects.get_or_create(
                filme=filme,
                data_hora=data_sessao,
                defaults={
                    'capacidade_total': 60,
                    'local': local_sessao,
                    'ativo': True
                }
            )
            sessoes_futuras.append(sessao)

        # Remove cópias criadas pela execução anterior do seed, mesmo que
        # os horários tenham alguns microssegundos de diferença.
        for filme in filmes_criados[:4]:
            mantidas = []
            for sessao in filme.session_set.filter(ativo=True).order_by('data_hora', 'pk'):
                anterior = next(
                    (
                        item for item in mantidas
                        if item.local == sessao.local
                        and item.capacidade_total == sessao.capacidade_total
                        and abs((item.data_hora - sessao.data_hora).total_seconds()) < 24 * 60 * 60
                    ),
                    None
                )
                if anterior:
                    for reserva in sessao.reservation_set.all():
                        if anterior.reservation_set.filter(usuario=reserva.usuario).exists():
                            reserva.delete()
                        else:
                            reserva.sessao = anterior
                            reserva.save(update_fields=['sessao'])
                    sessao.delete()
                else:
                    mantidas.append(sessao)

        # Atualiza a lista após a remoção das cópias, para que as reservas
        # sejam vinculadas apenas a sessões que continuam existindo.
        sessoes_futuras = [
            filme.session_set.filter(ativo=True, data_hora__gt=agora).order_by('data_hora').first()
            for filme in filmes_criados[:4]
        ]
        sessoes_futuras = [sessao for sessao in sessoes_futuras if sessao is not None]

        # Sessão Passada (para testar histórico e presenças)
        sessao_passada, _ = Session.objects.get_or_create(
            filme=filmes_criados[4],  # Ilha das Flores
            data_hora=agora - timedelta(days=3),
            defaults={
                'capacidade_total': 45,
                'local': 'Auditório Central - IFRN Campus Natal',
                'ativo': True
            }
        )

        self.stdout.write(self.style.SUCCESS('Sessões futuras e históricas configuradas com sucesso.'))

        # 6. Criar Reservas de exemplo
        usuario_aluno = danilo_user or aluno1

        # Reserva futura ativa
        if sessoes_futuras:
            res_futura, _ = Reservation.objects.get_or_create(
                usuario=usuario_aluno,
                sessao=sessoes_futuras[0],
                defaults={'status': 'reservado'}
            )
            Reservation.objects.get_or_create(
                usuario=aluno2,
                sessao=sessoes_futuras[0],
                defaults={'status': 'reservado'}
            )

        # Reservas no evento passado (uma presente, uma com falta justificada)
        Reservation.objects.get_or_create(
            usuario=usuario_aluno,
            sessao=sessao_passada,
            defaults={'status': 'presente'}
        )
        Reservation.objects.get_or_create(
            usuario=aluno1,
            sessao=sessao_passada,
            defaults={'status': 'presente'}
        )
        Reservation.objects.get_or_create(
            usuario=aluno2,
            sessao=sessao_passada,
            defaults={'status': 'falta_justificada', 'justificativa_cancelamento': 'Participação em congresso científico'}
        )

        self.stdout.write(self.style.SUCCESS('Reservas e presenças simuladas configuradas.'))

        # 7. Criar Comentários no Fórum
        filme_coment = filmes_criados[0]  # O Menino que Descobriu o Vento
        comentario_pai, _ = ForumComment.objects.get_or_create(
            filme=filme_coment,
            usuario=prof_user,
            texto='Prezados alunos, observem com atenção como o filme retrata o método científico e a curiosidade como ferramentas de transformação social. Teremos um debate ao final da sessão sobre energia renovável no semiárido potiguar.',
            defaults={'ativo': True}
        )

        ForumComment.objects.get_or_create(
            filme=filme_coment,
            usuario=usuario_aluno,
            parent=comentario_pai,
            texto='Professor Carlos, o protótipo que ele constrói no filme pode ser diretamente relacionado ao projeto integrador que estamos desenvolvendo em Eletrotécnica!',
            defaults={'ativo': True}
        )

        # 8. Notificações para os usuários
        for u in [usuario_aluno, aluno1]:
            Notification.objects.get_or_create(
                usuario=u,
                titulo='Bem-vindo ao Didacta Vision!',
                mensagem='As inscrições para a nova temporada de cinema científico do projeto Luz, Ciência e Ação estão abertas. Garanta sua vaga!',
                defaults={'tipo': 'info', 'lida': False}
            )
            Notification.objects.get_or_create(
                usuario=u,
                titulo='Lembrete de Sessão',
                mensagem='Sua reserva para a sessão de "O Menino que Descobriu o Vento" está confirmada. Chegue com 15 minutos de antecedência.',
                defaults={'tipo': 'sessao', 'lida': False}
            )

        self.stdout.write(self.style.SUCCESS('Notificações e fórum populados com sucesso.'))
        self.stdout.write(self.style.SUCCESS(
            '\n=======================================================\n'
            ' [SUCESSO] Sistema Didacta Vision populado e pronto!\n'
            ' - Catálogo de filmes educativos disponível.\n'
            ' - Sessões ativas e histórico de frequência configurados.\n'
            ' - Debate pedagógico no fórum registrado.\n'
            f' - Usuários de demonstração prontos (senha padrão: {demo_password}).\n'
            '======================================================='
        ))
