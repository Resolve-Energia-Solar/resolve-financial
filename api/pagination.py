from rest_framework.pagination import LimitOffsetPagination

class CustomLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 15  # Limite padrão se 'limit' não for especificado
    limit_query_param = 'limit'       # Nome do parâmetro para o limite
    offset_query_param = 'offset'     # Nome do parâmetro para o deslocamento
    max_limit = 100                   # Limite máximo permitido
