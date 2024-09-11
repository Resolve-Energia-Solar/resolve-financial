from django import template

register = template.Library()

@register.filter
def history_type_label(history_type):
    if history_type == '+':
        return 'Criado'
    elif history_type == '~':
        return 'Atualizado'
    elif history_type == '-':
        return 'Deletado'
    return 'Desconhecido'

register.filter('history_type_label', history_type_label)