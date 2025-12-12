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




