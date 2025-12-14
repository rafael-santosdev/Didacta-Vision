from django import template

register = template.Library()


@register.filter
def dict_get(value, key):
    """
    Retorna o valor de um dicionário para a chave informada.
    Útil para acessar reservas por sessão no template.
    """
    if value is None:
        return None
    try:
        return value.get(key)
    except AttributeError:
        return None


@register.simple_tag
def unread_notifications_count(user):
    """
    Retorna a contagem de notificações não lidas do usuário.
    """
    if not user or not user.is_authenticated:
        return 0
    try:
        return user.notification_set.filter(lida=False).count()
    except:
        return 0


@register.simple_tag
def unread_tickets_count(user):
    """
    Retorna a contagem de tickets não respondidos para admin.
    """
    if not user or not user.is_authenticated:
        return 0
    try:
        if hasattr(user, 'is_admin_or_professor') and user.is_admin_or_professor():
            from didacta.models import HelpTicket
            count = HelpTicket.objects.filter(status='aberto').count()
            return count
        return 0
    except Exception as e:
        return 0




