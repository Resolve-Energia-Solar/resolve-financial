from requests import Response
from accounts.models import User
from accounts.serializers import UserSerializer
from api.views import BaseModelViewSet
from .models import *
from .serializers import *
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime
from datetime import datetime
from django.db.models import Q
from collections import defaultdict


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
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if not self.request.user.is_superuser:
            user_groups = self.request.user.groups.values_list('id', flat=True)
            queryset = queryset.filter(groups__id__in=user_groups)
        return queryset.filter()


class FormsViewSet(BaseModelViewSet):
    queryset = Forms.objects.all()
    serializer_class = FormsSerializer


class AnswerViewSet(BaseModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer



class ScheduleViewSet(BaseModelViewSet):
    serializer_class = ScheduleSerializer

    def get_queryset(self):
        qs = Schedule.objects.select_related(
            'customer',
            'service',
            'final_service_opinion',
            'service_opinion',
            'project',
            'schedule_creator',
            'schedule_agent',
        )

        user = self.request.user

        # 1. Filtros Globais
        customer_icontains = self.request.query_params.get('customer_icontains')
        if customer_icontains:
            qs = qs.filter(
                Q(customer__complete_name__icontains=customer_icontains) |
                Q(customer__first_document__icontains=customer_icontains)
            )

        final_services_opnions = self.request.query_params.get('final_services_opnions')
        if final_services_opnions:
            opinions = final_services_opnions.split(',')
            qs = qs.filter(final_service_opinion__id__in=opinions)

        final_service_is_null = self.request.query_params.get('final_service_is_null')
        if final_service_is_null == 'true':
            qs = qs.filter(final_service_opinion__isnull=True)
        elif final_service_is_null == 'false':
            qs = qs.filter(final_service_opinion__isnull=False)

        service_opnion_is_null = self.request.query_params.get('service_opnion_is_null')
        if service_opnion_is_null == 'true':
            qs = qs.filter(service_opinion__isnull=True)
        elif service_opnion_is_null == 'false':
            qs = qs.filter(service_opinion__isnull=False)

        project = self.request.query_params.get('project_confirmed')
        if project:
            qs = qs.filter(project__id=project, status='Confirmado')

        service = self.request.query_params.get('service')
        if service:
            qs = qs.filter(service__id=service)

        # 2. Filtros por permissão
        if user.has_perm('field_services.view_all_schedule'):
            return qs

        # a) Stakeholder direto
        stakeholder_qs = qs.filter(
            Q(schedule_creator=user) |
            Q(schedule_agent=user) |
            Q(project__sale__seller=user)
        )

        # b) Unidades relacionadas
        if hasattr(user, 'employee') and user.employee.related_branches.exists() or user.branch_owners.exists():
            related_branch_ids = list(user.employee.related_branches.values_list('id', flat=True))
            branch_owner_ids = list(user.branch_owners.values_list('id', flat=True))
            branch_ids = related_branch_ids + branch_owner_ids

            branch_qs = qs.filter(
                Q(schedule_creator__employee__branch_id__in=branch_ids) |
                Q(project__sale__branch_id__in=branch_ids)
            )
        else:
            branch_qs = qs.none()

        return stakeholder_qs | branch_qs

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

        date_param = request.query_params.get('date')
        agent_param = request.query_params.get('agent')

        if date_param:
            date = parse_datetime(date_param).date()

        if agent_param:
            agents_qs = User.objects.filter(
                complete_name__icontains=agent_param,
                user_types__name='agent'
            )
        else:
            agents_qs = User.objects.filter(user_types__name='agent')

        agents = agents_qs.values_list('id', flat=True)
        agent_objs = agents_qs.in_bulk()

        schedules = Schedule.objects.filter(
            schedule_date=date,
            schedule_agent_id__in=agents
        )

        schedules_by_agent = defaultdict(list)
        for s in schedules:
            schedules_by_agent[s.schedule_agent_id].append(s)

        blocks = BlockTimeAgent.objects.filter(
            agent_id__in=agents,
            start_date=date
        )

        blocks_by_agent = defaultdict(list)
        for b in blocks:
            blocks_by_agent[b.agent_id].append(b)

        data = []

        for agent_id in agents:
            agent = agent_objs.get(agent_id)
            if not agent:
                continue

            agent_data = {
                'agent': {
                    'id': agent.id,
                    'name': agent.complete_name,
                    },
                'schedules': []
            }

            agent_schedules = schedules_by_agent.get(agent_id, [])
            agent_blocks = blocks_by_agent.get(agent_id, [])

            for start, end in hours:
                ocupado = any(
                    s.schedule_start_time.strftime('%H:%M') < end and
                    s.schedule_end_time.strftime('%H:%M') > start
                    for s in agent_schedules
                )
                if ocupado:
                    status_ = 'Ocupado'
                else:
                    bloqueado = any(
                        b.start_time.strftime('%H:%M') < end and
                        b.end_time.strftime('%H:%M') > start
                        for b in agent_blocks
                    )
                    status_ = 'Bloqueado' if bloqueado else 'Livre'

                agent_data['schedules'].append({
                    'start_time': start,
                    'end_time': end,
                    'status': status_
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
    
class ServiceOpinionViewSet(BaseModelViewSet):
    queryset = ServiceOpinion.objects.all()
    serializer_class = ServiceOpinionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        service = self.request.query_params.get('service')

        if service:
            queryset = queryset.filter(service__id=service)

        return queryset


class RouteViewSet(BaseModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer