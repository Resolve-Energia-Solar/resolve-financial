from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from functools import cached_property
from django.core.paginator import EmptyPage, PageNotAnInteger

class CustomLimitOffsetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    page_query_param = 'page'
    max_page_size = 100

    def get_page_size(self, request):
        try:
            size = int(request.query_params.get(self.page_size_query_param, self.page_size))
            return min(size, self.max_page_size)
        except (ValueError, TypeError):
            return self.page_size

    def paginate_queryset(self, queryset, request, view=None):
        self.page_size = self.get_page_size(request)
        if not self.page_size:
            return None

        paginator = self.django_paginator_class(queryset, self.page_size)
        page_number = request.query_params.get(self.page_query_param, 1)

        try:
            self.page = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            self.page = None
            return []

        return list(self.page)

    @cached_property
    def next_link(self):
        return self.get_next_link()

    @cached_property
    def previous_link(self):
        return self.get_previous_link()

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count if self.page else 0,
            'next': self.next_link if self.page else None,
            'previous': self.previous_link if self.page else None,
            'results': data
        })
