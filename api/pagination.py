from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100
    page_query_param = 'page'

    def __init__(self):
        super().__init__()
        self.extra_meta = {}

    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(queryset, request, view)
        except NotFound:
            self.page = None
            return []

    def get_paginated_response(self, data):
        if self.page is None:
            return Response({
                'results': [],
                'meta': {
                    'pagination': {
                        'page': None,
                        'limit': None,
                        'total_pages': 0,
                        'total_count': 0,
                        'next': None,
                        'previous': None,
                    },
                    **self.extra_meta
                }
            })

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
