from django.db import connection
from django.shortcuts import redirect
from django.urls import reverse

class CloseDBConnectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        connection.close()
        return response

class ProtectSilkMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/silk/'):
            if not request.user.is_authenticated or not request.user.is_staff:
                return redirect(reverse('admin:login') + f'?next={request.path}')
        return self.get_response(request)