from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

class CustomLimitOffsetPagination(PageNumberPagination):
    page_size = 15 
    page_size_query_param = 'limit' 
    page_query_param = 'page' 
    max_page_size = 100 

    def get_page_size(self, request):
        try:
            page_size = super().get_page_size(request)
            if page_size is None:
                return self.page_size
            return min(page_size, self.max_page_size)
        except (ValueError, TypeError):
            return self.page_size

    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(queryset, request, view)
        except NotFound:
            self.page = None
            return []

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count if self.page else 0,
            'next': self.get_next_link() if self.page else None,
            'previous': self.get_previous_link() if self.page else None,
            'results': data
        })
