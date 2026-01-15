import math

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class MyPageNumberPagination(PageNumberPagination):
    page_size = 5  # default page size

    # page_size_query_param = 'size'  # ?page=xx&size=??
    # max_page_size = 10  # max page size

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'results': data,
            'page_size': self.page_size,
            'totalPageNum': math.ceil(self.page.paginator.count / self.page_size)
        })
