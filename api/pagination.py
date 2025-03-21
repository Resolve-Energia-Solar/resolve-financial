from rest_framework.pagination import CursorPagination
from rest_framework.response import Response

class CustomCursorPagination(CursorPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100
    ordering = '-id'

    def get_page_size(self, request):
        if self.page_size_query_param:
            try:
                requested_page_size = int(request.query_params.get(self.page_size_query_param, self.page_size))
                if requested_page_size <= 0:
                    return self.page_size
                return min(requested_page_size, self.max_page_size)
            except (ValueError, TypeError):
                return self.page_size
        return self.page_size

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })