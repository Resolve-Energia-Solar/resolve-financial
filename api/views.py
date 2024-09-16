from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from accounts.models import *
from resolve_crm.models import *
from .serializers.accounts import *
from .serializers.resolve_crm import *
from .serializers.logistics import *
from .serializers.inspections import *
from .serializers.core import *
from rest_framework.permissions import IsAuthenticated, AllowAny
from accounts.models import User
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers.accounts import UserSerializer

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView


class UserLoginView(APIView):
    permission_classes = [AllowAny] 
    http_method_names = ['post']
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'id': user.id,
                    'username': user.username
                })
        except User.DoesNotExist:
            pass
        return Response({
            'message': 'Invalid credentials'
        }, status=400)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    
class LeadViewSet(ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]
    

class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    
class AttachmentViewSet(ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]


class SquadViewSet(ModelViewSet):
    queryset = Squad.objects.all()
    serializer_class = SquadSerializer
    permission_classes = [IsAuthenticated]
    
    
class DepartmentViewSet(ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]    
    

class BranchViewSet(ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]
    

class MarketingCampaignViewSet(ModelViewSet):
    queryset = MarketingCampaign.objects.all()
    serializer_class = MarketingCampaignSerializer
    permission_classes = [IsAuthenticated]


class AdressViewSet(ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]


class RoleViewSet(ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]


class FinancierViewSet(ModelViewSet):
    queryset = Financier.objects.all()
    serializer_class = FinancierSerializer
    permission_classes = [IsAuthenticated]

class MaterialTypesViewSet(ModelViewSet):
    queryset = MaterialTypes.objects.all()
    serializer_class = MaterialTypesSerializer
    permission_classes = [IsAuthenticated]
    

class MaterialsViewSet(ModelViewSet):
    queryset = Materials.objects.all()
    serializer_class = MaterialsSerializer
    permission_classes = [IsAuthenticated]


class SolarEnergyKitViewSet(ModelViewSet):
    queryset = SolarEnergyKit.objects.all()
    serializer_class = SolarEnergyKitSerializer
    permission_classes = [IsAuthenticated]
    

class RoofTypeViewSet(ModelViewSet):
    queryset = RoofType.objects.all()
    serializer_class = RoofTypeSerializer
    permission_classes = [IsAuthenticated]