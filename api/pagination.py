from rest_framework.pagination import PageNumberPagination

class CustomLimitOffsetPagination(PageNumberPagination):
    page_size = 15  # Limite padrão de itens por página
    page_size_query_param = 'limit'  # Nome do parâmetro para o limite
    page_query_param = 'page'  # Nome do parâmetro para a página
    max_page_size = 100  # Limite máximo de itens por página

    def get_page_size(self, request):
        try:
            page_size = super().get_page_size(request)
            if page_size is None:
                return self.page_size
            return min(page_size, self.max_page_size)
        except (ValueError, TypeError):
            return self.page_size