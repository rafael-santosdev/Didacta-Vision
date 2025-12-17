from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import logout


class AcessoProvisorioMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
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
        
        path = request.path
        for url in urls_permitidas:
            if path.startswith(url) or path == '/':
                return self.get_response(request)
        
        if request.user.is_authenticated:
            user = request.user
            
            if user.email_verificado:
                return self.get_response(request)
            
            if user.acesso_provisorio_expira:
                if timezone.now() > user.acesso_provisorio_expira:
                    logout(request)
                    messages.error(
                        request,
                        'Seu acesso provisório expirou. Para continuar utilizando o sistema, '
                        'é necessário verificar o e-mail. Por favor, faça login e verifique '
                        'o código enviado para seu e-mail.'
                    )
                    return redirect('didacta:login')
            else:
                if not user.is_superuser and not user.is_staff:
                    logout(request)
                    messages.error(
                        request,
                        'Para utilizar o sistema, é necessário verificar seu e-mail.'
                    )
                    return redirect('didacta:login')
        
        return self.get_response(request)
