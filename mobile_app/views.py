from core.serializers import AttachmentSerializer
from resolve_crm.models import Sale
from resolve_crm.serializers import SaleSerializer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

from api.views import BaseModelViewSet
from mobile_app.serializers import CustomerSerializer, MobileSaleSerializer


class CustomerLoginView(APIView):

    permission_classes = [AllowAny]
    http_method_names = ['post']

    def post(self, request):
        first_document = request.data.get('first_document')
        birth_date = request.data.get('birth_date')

        # Validar os campos recebidos
        if not first_document or not birth_date:
            return Response({
                'message': 'Documento e data de nascimento são obrigatórios.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(first_document=first_document, birth_date=birth_date)
        except User.DoesNotExist:
            return Response({
                'message': 'Usuário com esse documento e data de nascimento não encontrado.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Verificar se o usuário está ativo
        if not user.is_active:
            return Response({
                'message': 'Usuário inativo.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verificar se o usuário tem uma venda associada
        if not user.customer_sales.exists():
            return Response({
                'message': 'Cliente sem venda.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        last_login = user.last_login
        
        # Gerar e retornar os tokens JWT
        refresh = RefreshToken.for_user(user)
        
        # Atualizar o último login do usuário
        user.last_login = timezone.now()
        user.save()

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'id': user.id,
            'last_login': last_login
        }, status=status.HTTP_200_OK)


class CustomerViewset(BaseModelViewSet):
    queryset = User.objects.filter(is_active=True, customer_sales__isnull=False).distinct()
    serializer_class = CustomerSerializer
    http_method_names = ['get']


class SaleViewset(BaseModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = MobileSaleSerializer
    http_method_names = ['get']


class ContractView(APIView):

    http_method_names = ['get']

    def get(self, request, sale_id):
        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return Response({
                'message': 'Venda não encontrada.'
            }, status=status.HTTP_404_NOT_FOUND)

        missing_documents = sale.missing_documents()  # Chame o método aqui

        attached_documents = sale.attachments.all()
        last_attached_date = attached_documents.order_by('-created_at').first().created_at if attached_documents else None

        data = {
            'all_documents_present': not missing_documents,
            'missing_documents': missing_documents,
            'last_attached_date': last_attached_date,
            'attachments': AttachmentSerializer(attached_documents, many=True).data
        }

        return Response(data, status=status.HTTP_200_OK)
