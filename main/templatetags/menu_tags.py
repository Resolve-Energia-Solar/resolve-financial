from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def is_active_open(context, *paths):
    """
    Verifica se o caminho atual da requisição está entre os caminhos fornecidos.
    Se estiver, retorna a string 'active open', que pode ser usada para adicionar
    classes CSS a um elemento HTML, indicando que o item do menu deve ser exibido
    como ativo e aberto. Caso contrário, retorna uma string vazia.

    Args:
    - context: O contexto da template, que inclui detalhes da requisição atual.
    - *paths: Um ou mais caminhos de URL para verificar contra o caminho atual da requisição.

    Returns:
    - Uma string 'active open' se o caminho atual estiver entre os caminhos fornecidos,
        caso contrário, uma string vazia.
    """
    request = context['request']
    return 'active open' if request.path in paths else ''


@register.simple_tag(takes_context=True)
def is_active(context, *paths):
    """
    Verifica se o caminho atual da requisição corresponde exatamente ao caminho fornecido.
    Se corresponder, retorna a string 'active', que pode ser usada para adicionar
    classes CSS a um elemento HTML, indicando que o item do menu deve ser exibido
    como ativo. Caso contrário, retorna uma string vazia.

    Args:
    - context: O contexto da template, que inclui detalhes da requisição atual.
    - path: O caminho de URL para verificar contra o caminho atual da requisição.

    Returns:
    - Uma string 'active' se o caminho atual corresponder ao caminho fornecido,
            caso contrário, uma string vazia.
    """
    request = context['request']
    return 'active' if request.path in paths else ''
