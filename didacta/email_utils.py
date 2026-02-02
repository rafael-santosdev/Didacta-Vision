"""
Utilitário de envio de e-mail para o Didacta Vision.

Garante entrega do código de verificação em qualquer rede (IFRN ou externa):
- SMTP com timeout para não travar em redes que bloqueiam a porta.
- Fallback opcional via Mailgun (HTTPS), que costuma funcionar em redes institucionais.
"""
import logging
from django.conf import settings
from django.core.mail import get_connection, EmailMessage

logger = logging.getLogger(__name__)


def _send_via_smtp(recipient_list, subject, body, from_email=None):
    """Envia e-mail via SMTP com timeout configurável."""
    from_email = from_email or getattr(
        settings, 'DEFAULT_FROM_EMAIL', 'Didacta Vision <noreply@didactavision.local>'
    )
    timeout = getattr(settings, 'EMAIL_TIMEOUT', 10)
    connection = get_connection(
        backend=settings.EMAIL_BACKEND,
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        username=settings.EMAIL_HOST_USER or None,
        password=settings.EMAIL_HOST_PASSWORD or None,
        use_tls=settings.EMAIL_USE_TLS,
        fail_silently=False,
        timeout=timeout,
    )
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=recipient_list,
        connection=connection,
    )
    email.send(fail_silently=False)
    return True


def _send_via_mailgun(recipient_list, subject, body, from_email=None):
    """Envia e-mail via API Mailgun (HTTPS), útil em redes que bloqueiam SMTP."""
    import requests

    api_key = getattr(settings, 'EMAIL_MAILGUN_API_KEY', None)
    domain = getattr(settings, 'EMAIL_MAILGUN_DOMAIN', None)
    if not api_key or not domain:
        return False

    from_email = from_email or getattr(
        settings, 'DEFAULT_FROM_EMAIL', 'Didacta Vision <noreply@didactavision.local>'
    )
    # Mailgun espera "Name <email>" ou só email
    if isinstance(from_email, str) and '<' in from_email:
        mailgun_from = from_email
    else:
        mailgun_from = f"Didacta Vision <mailgun@{domain}>"

    url = f"https://api.mailgun.net/v3/{domain}/messages"
    auth = ('api', api_key)
    to_str = ','.join(recipient_list) if isinstance(recipient_list, (list, tuple)) else recipient_list
    data = {
        'from': mailgun_from,
        'to': to_str,
        'subject': subject,
        'text': body,
    }
    timeout = getattr(settings, 'EMAIL_TIMEOUT', 10)
    try:
        resp = requests.post(url, auth=auth, data=data, timeout=timeout)
        if resp.status_code in (200, 201):
            return True
        logger.warning('Mailgun API respondeu com status %s: %s', resp.status_code, resp.text)
        return False
    except requests.RequestException as e:
        logger.warning('Falha ao enviar via Mailgun: %s', e)
        return False


def send_verification_email(recipient_list, subject, body):
    """
    Envia e-mail de verificação com estratégia que funciona em IFRN e redes externas.

    Ordem:
    1. Se Mailgun estiver configurado, tenta Mailgun primeiro (HTTPS, porta 443).
    2. Caso contrário, ou se Mailgun falhar, tenta SMTP com timeout.

    Retorna:
        (True, None) se enviado com sucesso.
        (False, mensagem_erro) se não foi possível enviar.
    """
    if not recipient_list:
        return False, 'Nenhum destinatário informado.'

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)

    # 1) Tentar Mailgun primeiro se configurado (funciona em redes que bloqueiam SMTP)
    if getattr(settings, 'EMAIL_MAILGUN_API_KEY', None) and getattr(settings, 'EMAIL_MAILGUN_DOMAIN', None):
        if _send_via_mailgun(recipient_list, subject, body, from_email):
            return True, None
        # Se Mailgun falhou e está configurado como único, não tenta SMTP
        if getattr(settings, 'EMAIL_MAILGUN_ONLY', False):
            return False, 'Envio por e-mail temporariamente indisponível. Use o código temporário na próxima tela.'

    # 2) Tentar SMTP (com timeout para não travar em redes que bloqueiam a porta)
    if getattr(settings, 'EMAIL_HOST_USER', None) and getattr(settings, 'EMAIL_HOST_PASSWORD', None):
        try:
            _send_via_smtp(recipient_list, subject, body, from_email)
            return True, None
        except Exception as e:
            logger.warning('Falha ao enviar via SMTP: %s', e)
            # Se Mailgun não foi tentado antes, tentar como fallback
            if not getattr(settings, 'EMAIL_MAILGUN_API_KEY', None):
                return False, str(e) or 'Falha no envio. Use o código temporário na próxima tela.'
            return False, str(e) or 'Falha no envio. Use o código temporário na próxima tela.'

    return False, 'Envio de e-mail não configurado. Use o código temporário na próxima tela.'
