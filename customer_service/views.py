from django.contrib.auth import get_user_model
from rest_framework.authentication import (
    TokenAuthentication,
    BasicAuthentication,
    SessionAuthentication,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.views import BaseModelViewSet
from customer_service.models import CustomerService
from customer_service.serializers import CustomerServiceSerializer

User = get_user_model()


class CustomerServiceViewSet(BaseModelViewSet):
    serializer_class = CustomerServiceSerializer
    queryset = CustomerService.objects.all()
    authentication_classes = [
        TokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
        JWTAuthentication,
    ]

    def create(self, request, *args, **kwargs):
        document = request.data.get("document")
        warning = None
        customer = None

        if document:
            try:
                customer = User.objects.get(first_document=document)
            except User.DoesNotExist:
                warning = "Usuário não encontrado com este documento."

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(customer=customer)

        data = serializer.data
        if warning:
            data["warning"] = warning

        return Response(
            data, status=status.HTTP_201_CREATED, headers=self.get_success_headers(data)
        )
