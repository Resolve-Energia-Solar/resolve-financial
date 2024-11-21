from rest_framework.pagination import PageNumberPagination

class AttachmentPagination(PageNumberPagination):
    page_size = 20  # Define o limite de itens por página
    page_size_query_param = 'page_size'  # Permite personalizar o tamanho via query params
    max_page_size = 100  # Limite máximo para paginação personalizada
