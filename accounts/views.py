import os
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.db.models import Case, When, Value, FloatField, IntegerField, Q
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_time
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from geopy.distance import geodesic

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.models import *
from accounts.serializers import *
from api.views import BaseModelViewSet
from accounts.serializers import PasswordResetConfirmSerializer
from field_services.models import BlockTimeAgent, Category, FreeTimeAgent, Schedule

# Accounts views

class UserLoginView(APIView):
    permission_classes = [AllowAny]
    http_method_names = ['post']

    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        # Validar os campos recebidos
        if not email or not password:
            return Response({
                'message': 'Email e senha são obrigatórios.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'message': 'Usuário com esse email não encontrado.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar se o usuário está ativo
        if not user.is_active:
            return Response({
                'message': 'Usuário inativo.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_superuser and not user.employee:
            return Response({
                'message': 'Usuário não é um funcionário.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Verificar senha
        if not user.check_password(password):
            return Response({
                'message': 'Senha incorreta.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
            'username': user.username,
            'last_login': last_login,
        }, status=status.HTTP_200_OK)


class UserTokenRefreshView(TokenRefreshView):
    http_method_names = ['post']
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


def calculate_distance(lat1, lon1, lat2, lon2):
    distance = geodesic((lat1, lon1), (lat2, lon2)).kilometers
    return distance


from django.utils.dateparse import parse_time
from django.utils import timezone
from django.db.models import OuterRef, Subquery, Count, Value
from django.db.models.functions import Coalesce

class UserViewSet(BaseModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'post', 'put', 'delete', 'patch']

    def get_queryset(self):
        queryset = super().get_queryset()

        queryset = queryset.select_related('employee').all()
        
        # Parâmetros de filtro
        name = self.request.query_params.get('name')
        user_type = self.request.query_params.get('type')
        email = self.request.query_params.get('email')
        phone = self.request.query_params.get('phone')
        person_type = self.request.query_params.get('person_type')
        first_document = self.request.query_params.get('first_document')
        second_document = self.request.query_params.get('second_document')
        category = self.request.query_params.get('category')
        date = self.request.query_params.get('date')
        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')
        order_by_schedule_count = self.request.query_params.get('order_by_schedule_count')

        if name:
            queryset = queryset.filter(complete_name__icontains=name)
        if user_type:
            queryset = queryset.filter(user_types__name=user_type)
        if email:
            queryset = queryset.filter(email__icontains=email)
        if phone:
            queryset = queryset.filter(phone__number__icontains=phone)
        if person_type:
            queryset = queryset.filter(person_type=person_type)
        if first_document:
            queryset = queryset.filter(first_document__icontains=first_document)
        if second_document:
            queryset = queryset.filter(second_document__icontains=second_document)
        if category:
            queryset = queryset.filter(
                id__in=Category.objects.get(id=category).members.values_list('id', flat=True)
            )

        if date and start_time and end_time:
            blocked_agents = BlockTimeAgent.objects.filter(
                start_date__lte=date,
                end_date__gte=date,
                start_time__lt=parse_time(end_time),
                end_time__gt=parse_time(start_time)
            ).values_list('agent', flat=True)
            queryset = queryset.exclude(id__in=blocked_agents)

            day_of_week = timezone.datetime.strptime(date, '%Y-%m-%d').weekday()
            free_agents_ids = FreeTimeAgent.objects.filter(
                day_of_week=day_of_week,
                start_time__lt=parse_time(end_time),
                end_time__gt=parse_time(start_time)
            ).values_list('agent_id', flat=True).distinct()
            queryset = queryset.filter(id__in=free_agents_ids)

            overlapping_schedules = Schedule.objects.filter(
                schedule_date=date,
                schedule_start_time__lt=parse_time(end_time),
                schedule_end_time__gt=parse_time(start_time),
                schedule_agent_id__isnull=False
            ).values_list('schedule_agent_id', flat=True)
            queryset = queryset.exclude(id__in=overlapping_schedules)

        if date and category and order_by_schedule_count:
            daily_schedules_subquery = Schedule.objects.filter(
                schedule_agent=OuterRef('pk'),
                schedule_date=date
            ).values('schedule_agent').annotate(cnt=Count('id')).values('cnt')[:1]

            queryset = queryset.annotate(
                daily_schedules_count=Coalesce(Subquery(daily_schedules_subquery), Value(0))
            )

            if order_by_schedule_count == 'asc':
                queryset = queryset.order_by('daily_schedules_count')
            elif order_by_schedule_count == 'desc':
                queryset = queryset.order_by('-daily_schedules_count')

        return queryset


class EmployeeViewSet(BaseModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    http_method_names = ['get', 'post', 'put', 'delete', 'patch']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user')

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = serializer.save()
        return Response(EmployeeSerializer(employee).data, status=status.HTTP_201_CREATED)


class SquadViewSet(BaseModelViewSet):
    queryset = Squad.objects.all()
    serializer_class = SquadSerializer
    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset
    
 
class DepartmentViewSet(BaseModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    

class BranchViewSet(BaseModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer


class AddressViewSet(BaseModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('q')
        customer = self.request.query_params.get('customer_id')
        
        if customer:
            queryset = queryset.filter(customer_addresses__id=customer)

        if search:
            queryset = queryset.filter(
                Q(zip_code__icontains=search) |
                Q(country__icontains=search) |
                Q(state__icontains=search) |
                Q(city__icontains=search) |
                Q(neighborhood__icontains=search) |
                Q(street__icontains=search) |
                Q(number__icontains=search) |
                Q(complement__icontains=search)
            )

        return queryset
    

class PhoneNumberViewSet(BaseModelViewSet):
    queryset = PhoneNumber.objects.all()
    serializer_class = PhoneNumberSerializer


class RoleViewSet(BaseModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


class PermissionViewSet(BaseModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer


class GroupViewSet(BaseModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    

class CustomFieldViewSet(BaseModelViewSet):
    queryset = CustomField.objects.all()
    serializer_class = CustomFieldSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user__id=user_id)
        return queryset


@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetRequestView(GenericAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        if not email:
            raise ValidationError({"email": "Email é obrigatório."})
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Não informar se o e-mail não existe
            return Response({"detail": "E-mail de redefinição de senha enviado com sucesso."}, status=status.HTTP_200_OK)
        
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)

        reset_url = os.getenv("FRONTEND_RESET_PASSWORD_URL", "")
        
        if not reset_url:
            return Response({"detail": "URL de redefinição de senha não configurada."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        reset_url_with_token = f"{reset_url}?token={token}&uid={user.pk}"

        # Envie o e-mail usando um template HTML
        context = {
            'invitation_link': reset_url_with_token,
            'user': user,
        }
        subject = 'Reset de senha'
        html_content = render_to_string('invitation-email.html', context)
        
        # Configura o e-mail como HTML
        email = EmailMessage(
            subject=subject,
            body=html_content,
            to=[user.email]
        )
        email.content_subtype = "html"
        send_mail(
            subject=subject,
            message='',
            from_email=None,
            recipient_list=[user.email],
            html_message=html_content,
        )
        
        return Response({"detail": "E-mail de redefinição de senha enviado com sucesso."}, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetConfirmView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        uid = serializer.validated_data["uid"]
        new_password = serializer.validated_data["new_password"]

        try:
            user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            return Response({"detail": "Usuário inválido."}, status=status.HTTP_404_NOT_FOUND)

        token_generator = PasswordResetTokenGenerator()

        if not token_generator.check_token(user, token):
            return Response({"detail": "Token inválido ou expirado."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Senha alterada com sucesso."}, status=status.HTTP_200_OK)