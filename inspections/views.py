from datetime import timezone

from requests import Response
from api.views import BaseModelViewSet
from .models import *
from .serializers import *
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime
from datetime import datetime
from .consumers import LocationConsumer


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
    def get_timeline(self, request):
        date = datetime.now().date()
        hours = [
            ('09:00', '10:30'),
            ('10:30', '12:00'),
            ('13:00', '14:30'),
            ('14:30', '16:00'),
            ('16:00', '17:30'),
            ('17:30', '19:00'), 
        ]

        agents = []

        date_param = request.query_params.get('date')
        agent_param = request.query_params.get('agent')

        if date_param:
            date = parse_datetime(request.query_params['date']).date()

        if agent_param:
            agents = User.objects.filter(complete_name__icontains=agent_param, user_types__name='agent').values_list('id', flat=True)
        else:
            agents = User.objects.filter(user_types__name='agent').values_list('id', flat=True)

        schedules = Schedule.objects.filter(schedule_date=date).order_by('schedule_agent', 'schedule_start_time')

        data = []

        for agent in agents:
            agent_schedules = schedules.filter(schedule_agent=agent)
            agent_serializer = UserSerializer(User.objects.get(id=agent))
            agent_data = {
                'agent': agent_serializer.data,
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
                    # verifica se o agente tem bloqueio de horário
                    block_time = BlockTimeAgent.objects.filter(agent=agent, start_time__lt=end, end_time__gt=start, start_date=date)
                    if block_time.exists():
                        agent_data['schedules'].append({
                            'start_time': start,
                            'end_time': end,
                            'status': 'Bloqueado'
                        })
                    else:
                        agent_data['schedules'].append({
                            'start_time': start,
                            'end_time': end,
                            'status': 'Livre'
                        })
            data.append(agent_data)
            
        return Response(data, status=status.HTTP_200_OK)
    

class BlockTimeAgentViewSet(BaseModelViewSet):
    queryset = BlockTimeAgent.objects.all()
    serializer_class = BlockTimeAgentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        agent = self.request.query_params.get('agent')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if agent:
            queryset = queryset.filter(agent__id=agent)
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)

        return queryset
    
class FreeTimeAgentViewSet(BaseModelViewSet):
    queryset = FreeTimeAgent.objects.all()
    serializer_class = FreeTimeAgentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        agent = self.request.query_params.get('agent')
        day_of_week = self.request.query_params.get('day_of_week')

        if agent:
            queryset = queryset.filter(agent__id=agent)
        if day_of_week:
            queryset = queryset.filter(day_of_week=day_of_week)

        return queryset
    
class FormFileViewSet(BaseModelViewSet):
    queryset = FormFile.objects.all()
    serializer_class = FormFileSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        answer = self.request.query_params.get('answer')
        field_id = self.request.query_params.get('field_id')

        if answer:
            queryset = queryset.filter(answer__id=answer)
        if field_id:
            queryset = queryset.filter(field_id=field_id)

        return queryset


