from datetime import timezone

from requests import Response
from api.views import BaseModelViewSet
from .models import *
from .serializers import *
from rest_framework.decorators import action
from rest_framework import status
from django.utils.dateparse import parse_datetime


class RoofTypeViewSet(BaseModelViewSet):
    queryset = RoofType.objects.all()
    serializer_class = RoofTypeSerializer


class CategoryViewSet(BaseModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset
    
class DeadlineViewSet(BaseModelViewSet):
    queryset = Deadline.objects.all()
    serializer_class = DeadlineSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset

class ServiceViewSet(BaseModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


class FormsViewSet(BaseModelViewSet):
    queryset = Forms.objects.all()
    serializer_class = FormsSerializer


class AnswerViewSet(BaseModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer


class ScheduleViewSet(BaseModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        project = self.request.query_params.get('project')
        service = self.request.query_params.get('service')
        schedule_agent = self.request.query_params.get('schedule_agent')

        if project:
            queryset = queryset.filter(project__id=project)
        if service:
            queryset = queryset.filter(service__id=service)
        if schedule_agent:
            queryset = queryset.filter(schedule_agent__id=schedule_agent)

        return queryset

    # listar agendamentos por pessoa para timeline
    @action(detail=False, methods=['get'])
    def get_schedule_person(self, request):
        today = timezone.now().date()
        hours = [
            ('09:00', '10:30'),
            ('10:30', '12:00'),
            ('13:00', '14:30'),
            ('14:30', '16:00'),
            ('16:00', '17:30'),
            ('17:30', '19:00'), 
        ]

        schedules = Schedule.objects.filter(schedule_date=today).order_by('schedule_agent', 'schedule_start_time')
        agents = schedules.values_list('schedule_agent', flat=True).distinct()
        data = []

        for agent in agents:
            agent_schedules = schedules.filter(schedule_agent=agent)
            agent_data = {
                'agent': agent,
                'schedules': []
            }
            for start, end in hours:
                if agent_schedules.filter(schedule_start_time__lt=end, schedule_end_time__gt=start).exists():
                    agent_data['schedules'].append({
                        'start_time': start,
                        'end_time': end,
                        'status': 'Ocupado'
                    })
                else:
                    agent_data['schedules'].append({
                        'start_time': start,
                        'end_time': end,
                        'status': 'Livre'
                    })
            data.append(agent_data)
            
        return Response(data, status=status.HTTP_200_OK)
        