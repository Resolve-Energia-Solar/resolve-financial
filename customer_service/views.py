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
from customer_service.models import CustomerService, LostReason, Ticket, TicketType
from customer_service.serializers import (
    CustomerServiceSerializer,
    LostReasonSerializer,
    TicketSerializer,
    TicketTypeSerializer,
)
from rest_framework import serializers
from django.db.models import Count
from django.http import JsonResponse

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


class LostReasonViewSet(BaseModelViewSet):
    serializer_class = LostReasonSerializer
    queryset = LostReason.objects.all()
    authentication_classes = [
        TokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
        JWTAuthentication,
    ]


class TicketTypeViewSet(BaseModelViewSet):
    serializer_class = TicketTypeSerializer
    queryset = TicketType.objects.all()
    authentication_classes = [
        TokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
        JWTAuthentication,
    ]


class TicketViewSet(BaseModelViewSet):
    serializer_class = TicketSerializer
    queryset = Ticket.objects.select_related(
        "project",
        "responsible",
        "ticket_type",
        "responsible_department",
        "responsible_user",
    )
    authentication_classes = [
        TokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
        JWTAuthentication,
    ]

    def perform_create(self, serializer):
        user = self.request.user
        employee = getattr(user, "employee", None)
        ticket_type = serializer.validated_data.get("ticket_type")

        print(f"User: {user}, Employee: {employee}, Ticket Type: {ticket_type}")

        if not ticket_type or not getattr(ticket_type, "deadline", None):
            raise serializers.ValidationError(
                "O tipo de chamado deve ter um prazo definido."
            )
        if not employee:
            raise serializers.ValidationError(
                "Usuário não está cadastrado como funcionário."
            )

        print(f"Employee Department: {employee.department}")

        if not employee.department:
            raise serializers.ValidationError(
                "Funcionário não está vinculado a um Setor."
            )

        serializer.save(
            responsible=user,
            responsible_department=employee.department,
            deadline=ticket_type.deadline,
            current_user=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(current_user=self.request.user)


def tickets_por_departamento(request):
    """
    Retorna JSON no formato:
    [
      { "department": "TI", "count": 12 },
      { "department": "Suporte", "count": 8 },
      ...
    ]
    """
    qs = (
        Ticket.objects.values("responsible_department__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    data = [
        {"department": item["responsible_department__name"], "count": item["count"]}
        for item in qs
    ]
    return JsonResponse(data, safe=False)
