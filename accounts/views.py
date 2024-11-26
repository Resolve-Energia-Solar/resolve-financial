from django.utils import timezone
from django.db.models import Case, When, Value, FloatField, IntegerField, Q
from django.utils.dateparse import parse_time

from geopy.distance import geodesic
from inspections.models import Category, Schedule
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.models import *
from accounts.serializers import *
from api.views import BaseModelViewSet


# Accounts views

class UserLoginView(APIView):
    permission_classes = [AllowAny]
    http_method_names = ['post']

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


class UserViewSet(BaseModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'post', 'put', 'delete', 'patch']
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        user_type = self.request.query_params.get('type')
        email = self.request.query_params.get('email')
        phone = self.request.query_params.get('phone')
        branch = self.request.query_params.get('branch')
        department = self.request.query_params.get('department')
        role = self.request.query_params.get('role')
        person_type = self.request.query_params.get('person_type')
        first_document = self.request.query_params.get('first_document')
        second_document = self.request.query_params.get('second_document')
        category = self.request.query_params.get('category')
        date = self.request.query_params.get('date')
        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')
        latitude = self.request.query_params.get('latitude')
        longitude = self.request.query_params.get('longitude')

        if name:
            queryset = queryset.filter(complete_name__icontains=name)
        if user_type:
            queryset = queryset.filter(user_types__name=user_type)
        if email:
            queryset = queryset.filter(email__icontains=email)
        if phone:
            queryset = queryset.filter(phone__number__icontains=phone)
        if branch:
            queryset = queryset.filter(branch__name__icontains=branch)
        if department:
            queryset = queryset.filter(department__name__icontains=department)
        if role:
            queryset = queryset.filter(role__name__icontains=role)
        if person_type:
            queryset = queryset.filter(person_type=person_type)
        if first_document:
            queryset = queryset.filter(first_document__icontains=first_document)
        if second_document:
            queryset = queryset.filter(second_document__icontains=second_document)
        if category:
            queryset = queryset.filter(id__in=Category.objects.get(id=category).members.values_list('id', flat=True))

            if date and start_time and end_time:
                overlapping_schedules = Schedule.objects.filter(
                    schedule_date=date,
                    schedule_start_time__lt=parse_time(end_time),
                    schedule_end_time__gt=parse_time(start_time)
                ).values_list('schedule_agent_id', flat=True)

                queryset = queryset.exclude(id__in=overlapping_schedules)

                if latitude and longitude:
                    latitude = float(latitude)
                    longitude = float(longitude)

                    users_distance = []
                    for user in queryset:
                        last_schedule = Schedule.objects.filter(
                            schedule_agent=user,
                            schedule_date=date
                        ).order_by('-schedule_end_time').first()

                        user.distance = (
                            calculate_distance(latitude, longitude, last_schedule.latitude, last_schedule.longitude)
                            if last_schedule else None
                        )

                        users_distance.append((user, user.distance))

                        daily_schedules_count = Schedule.objects.filter(
                            schedule_agent=user,
                            schedule_date=date
                        ).count()
                        user.daily_schedules_count = daily_schedules_count

                    ordered_users = sorted(users_distance, key=lambda x: (x[1] is None, x[1]))
                    ordered_ids = [user[0].id for user in ordered_users]

                    queryset = queryset.filter(id__in=ordered_ids).annotate(
                        distance=Case(
                            *[When(id=user.id, then=Value(user.distance)) for user, _ in users_distance],
                            default=Value(None),  
                            output_field=FloatField()  
                        ),
                        daily_schedules_count=Case(
                            *[When(id=user.id, then=Value(user.daily_schedules_count)) for user in queryset],
                            default=Value(0),
                            output_field=IntegerField()  
                        )
                    ).order_by(
                        Case(
                            *[When(id=user_id, then=pos) for pos, user_id in enumerate(ordered_ids)]
                        )
                    )
        return queryset
    
    
class EmployeeViewSet(BaseModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    http_method_names = ['get', 'post', 'put', 'delete', 'patch']

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