from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100
    page_query_param = 'page'

    def __init__(self):
        super().__init__()
        self.extra_meta = {}

    def get_paginated_response(self, data):
        return Response({
            'meta': {
                'pagination': {
                    'page': self.page.number,
                    'limit': self.page.paginator.per_page, 
                    'total_pages': self.page.paginator.num_pages,
                    'total_count': self.page.paginator.count,
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                },
                **self.extra_meta 
            },
            'results': data
        })
