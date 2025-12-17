from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import logout


class AcessoProvisorioMiddleware:
    """
    Middleware para verificar se o acesso provisório do usuário expirou.
    Se expirou, bloqueia o acesso e redireciona para verificação de e-mail.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # URLs que não devem ser bloqueadas
        urls_permitidas = [
            '/login/',
            '/logout/',
            '/register/',
            '/verify-code/',
            '/password-reset/',
            '/admin/',
            '/static/',
            '/media/',
        ]
        
        # Verificar se é uma URL permitida
        path = request.path
        for url in urls_permitidas:
            if path.startswith(url) or path == '/':
                return self.get_response(request)
        
        # Verificar se o usuário está autenticado
        if request.user.is_authenticated:
            user = request.user
            
            # Se o e-mail já está verificado, permitir acesso
            if user.email_verificado:
                return self.get_response(request)
            
            # Se está em acesso provisório, verificar expiração
            if user.acesso_provisorio_expira:
                if timezone.now() > user.acesso_provisorio_expira:
                    # Acesso provisório expirou
                    logout(request)
                    messages.error(
                        request,
                        'Seu acesso provisório expirou. Para continuar utilizando o sistema, '
                        'é necessário verificar o e-mail. Por favor, faça login e verifique '
                        'o código enviado para seu e-mail.'
                    )
                    return redirect('didacta:login')
            else:
                # Usuário sem e-mail verificado e sem acesso provisório
                # Isso não deveria acontecer, mas por segurança, bloqueia
                if not user.is_superuser and not user.is_staff:
                    logout(request)
                    messages.error(
                        request,
                        'Para utilizar o sistema, é necessário verificar seu e-mail.'
                    )
                    return redirect('didacta:login')
        
        return self.get_response(request)


