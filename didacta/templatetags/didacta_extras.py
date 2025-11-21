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




