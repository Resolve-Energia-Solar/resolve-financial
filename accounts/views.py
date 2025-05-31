import os
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.db.models import Case, When, Value, FloatField, IntegerField, Q, Prefetch
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
from accounts.task import send_login_info_logs
from api.views import BaseModelViewSet
from accounts.serializers import PasswordResetConfirmSerializer
from field_services.models import BlockTimeAgent, Category, FreeTimeAgent, Schedule, Service
from django.utils.dateparse import parse_time
from django.utils import timezone
from django.db.models import OuterRef, Subquery, Count, Value
from django.db.models.functions import Coalesce
import datetime
from django.shortcuts import get_object_or_404
from django.db.models import OuterRef, Exists
from django.utils.dateparse import parse_date, parse_time
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.serializers import UserLoginSerializer
from resolve_crm.models import Project


# Accounts views

class UserLoginView(APIView):
    permission_classes = [AllowAny]
    http_method_names = ['post']

    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'message': 'Email e senha são obrigatórios.'}, status=400)

        try:
            user = User.objects.select_related(
                "employee", "employee__user_manager", "employee__department", "employee__role"
            ).prefetch_related("groups", "user_permissions").get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'Usuário não encontrado.'}, status=400)
        
        try:
            employee = user.employee
        except Employee.DoesNotExist:
            return Response({'message': 'Usuário não é um funcionário.'}, status=400)

        if not user.is_active:
            return Response({'message': 'Usuário inativo.'}, status=400)

        if not user.check_password(password):
            return Response({'message': 'Senha incorreta.'}, status=400)

        refresh = RefreshToken.for_user(user)
        last_login = user.last_login

        user.last_login = timezone.now()
        user.save()

        user_data = UserLoginSerializer(user).data

        send_login_info_logs.delay(
            user.id,
            user.email,
            user.complete_name,
            str(last_login) if last_login else None,
            request.META.get('REMOTE_ADDR', 'unknown')
        )

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "last_login": str(last_login) if last_login else None,
            "user": user_data,
        })
        
        
class UserTokenRefreshView(TokenRefreshView):
    http_method_names = ['post']
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


def calculate_distance(lat1, lon1, lat2, lon2):
    distance = geodesic((lat1, lon1), (lat2, lon2)).kilometers
    return distance


class UserViewSet(BaseModelViewSet):
    queryset = User.objects.all().select_related('employee', 'employee__user_manager', 'employee__department', 'employee__role').prefetch_related(
        'phone_numbers',
        'user_types',
        'addresses',
        'attachments',
        'employee__related_branches',
        'free_times',
        'block_times'
    ).defer('groups', 'user_permissions')
    serializer_class = UserSerializer
    http_method_names = ['get', 'post', 'put', 'delete', 'patch']

    def get_queryset(self):
        qs = super().get_queryset()
        # filtros simples
        params = self.request.query_params
        if params.get('name'):
            qs = qs.filter(complete_name__icontains=params['name'])
        if params.get('type'):
            qs = qs.filter(user_types__name=params['type'])
        if params.get('email'):
            qs = qs.filter(email__icontains=params['email'])
        if params.get('phone'):
            qs = qs.filter(phone__number__icontains=params['phone'])
        if params.get('person_type'):
            qs = qs.filter(person_type=params['person_type'])
        if params.get('first_document'):
            qs = qs.filter(first_document__icontains=params['first_document'])
        if params.get('second_document'):
            qs = qs.filter(second_document__icontains=params['second_document'])
        if params.get('category'):
            qs = qs.filter(
                id__in=Category.objects.get(id=params['category'])
                                  .members.values_list('id', flat=True)
            )
        if params.get('role'):
            qs = qs.filter(employee__role__name__icontains=params['role']).distinct()

        return qs

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        user = self.get_object()
        params = request.query_params
        date_str = params.get('date')
        start_str = params.get('start_time')
        end_str   = params.get('end_time')

        if not all([date_str, start_str, end_str]):
            return Response(
                {'detail': 'Parâmetros date, start_time e end_time são obrigatórios.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # parse
        try:
            day = parse_date(date_str).weekday()
            start_time = parse_time(start_str)
            end_time   = parse_time(end_str)
        except Exception:
            return Response(
                {'detail': 'Formato de data ou hora inválido.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # subqueries para este único usuário
        blocked_sq = BlockTimeAgent.objects.filter(
            agent=user,
            start_date__lte=date_str,
            end_date__gte=date_str,
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        free_sq = FreeTimeAgent.objects.filter(
            agent=user,
            is_deleted=False,
            day_of_week=day,
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        overlap_sq = Schedule.objects.filter(
            schedule_agent=user,
            schedule_date=date_str,
            schedule_start_time__lt=end_time,
            schedule_end_time__gt=start_time
        )
        
        # monta lista de slots livres daquele dia para esse agente
        free_qs = FreeTimeAgent.objects.filter(
            agent=user,
            is_deleted=False,
            day_of_week=day,
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).values('start_time', 'end_time')

        # 2) formata para string HH:MM
        free_time_agent = [
            {
                'start_time': slot['start_time'].strftime('%H:%M'),
                'end_time':   slot['end_time'].strftime('%H:%M'),
            }
            for slot in free_qs
        ]

        # executa EXISTS
        is_blocked    = blocked_sq.exists()
        has_free_slot = free_sq.exists()
        has_overlap   = overlap_sq.exists()

        available = (not is_blocked) and has_free_slot and (not has_overlap)

        data = {
            'user_id': user.id,
            'date': date_str,
            'start_time': start_str,
            'end_time': end_str,
            'is_blocked': is_blocked,
            'has_free_slot': has_free_slot,
            'has_overlap': has_overlap,
            'available': available,
            'free_time_agent': free_time_agent,
        }

        return Response(data, status=status.HTTP_200_OK)


    @action(detail=False, methods=['get'], url_path='available')
    def available(self, request):
        complete_name = request.query_params.get('complete_name')
        date_str      = request.query_params.get('date')
        start_str     = request.query_params.get('start_time')
        end_str       = request.query_params.get('end_time')
        service_id    = request.query_params.get('service')

        if not all([date_str, start_str, end_str, service_id]):
            return Response(
                {'detail': 'Parâmetros date, start_time, end_time e service são obrigatórios.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            day        = parse_date(date_str).weekday()
            start_time = parse_time(start_str)
            end_time   = parse_time(end_str)
        except Exception:
            return Response(
                {'detail': 'Formato inválido. Use YYYY-MM-DD e HH:MM.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = get_object_or_404(Service, pk=service_id)
        cat_id  = service.category.id
        
        if not cat_id:
            return Response(
                {'detail': 'Serviço não possui categoria associada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        blocked_sq = BlockTimeAgent.objects.filter(
            agent=OuterRef('pk'),
            start_date__lte=date_str, end_date__gte=date_str,
            start_time__lt=end_time, end_time__gt=start_time
        )
        free_sq = FreeTimeAgent.objects.filter(
            agent=OuterRef('pk'),
            is_deleted=False, day_of_week=day,
            start_time__lt=end_time, end_time__gt=start_time
        )
        overlap_sq = Schedule.objects.filter(
            schedule_agent=OuterRef('pk'),
            schedule_date=date_str,
            schedule_start_time__lt=end_time,
            schedule_end_time__gt=start_time
        )

        # começa o QS apenas pela categoria
        qs = User.objects.filter(categories__id=cat_id)

        # só aplica filtro por nome se vier algo não‐vazio
        if complete_name:
            qs = qs.filter(complete_name__icontains=complete_name)

        # aplica disponibilidade e contagem
        qs = (
            qs
            .annotate(
                is_blocked=Exists(blocked_sq),
                has_free_slot=Exists(free_sq),
                has_overlap=Exists(overlap_sq),
            )
            .filter(
                is_blocked=False,
                has_free_slot=True,
                has_overlap=False,
            )
            .annotate(
                schedule_count=Count(
                    'schedule_agent',
                    filter=Q(schedule_agent__schedule_date=date_str)
                )
            )
            .distinct()
            .values('id', 'complete_name', 'schedule_count')
        )

        return Response(list(qs), status=status.HTTP_200_OK)



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
        project_customer = self.request.query_params.get('project_customer_id')
        
        if project_customer:
            project = get_object_or_404(Project, id=project_customer)
            
            try:
                customer_id = project.sale.customer.id if project.sale.customer else None
            except AttributeError:
                customer_id = None
            
            queryset = queryset.filter(customer_addresses__id=customer_id)

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
    
    
class UserTypeViewSet(BaseModelViewSet):
    queryset = UserType.objects.all()
    serializer_class = UserTypeSerializer
    http_method_names = ['get', 'post', 'put', 'delete', 'patch']