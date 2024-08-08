from django.urls import path

from .views import *

app_name = 'resolve_crm'
urlpatterns = [

    # Tasks
    path('tarefas/', TasksView.as_view(), name='tasks'),
    path('tarefas/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('tarefas/criar/', TaskCreateView.as_view(), name='task-create'),
    path('tarefas/<int:pk>/editar/', TaskUpdateView.as_view(), name='task-update'),

    # Leads
    path('leads/criar/', LeadCreateView.as_view(), name='lead_create'),
    path('leads/', LeadListView.as_view(), name='lead_list'),
    path('leads/<int:pk>/', LeadDetailView.as_view(), name='lead_detail'),
    path('leads/<int:pk>/editar/', LeadUpdateView.as_view(), name='lead_update'),

    # ComercialProposal
    path('proposta/<int:pk>/', ComercialProposalDetailView, name='proposal_detail'),
    # path('proposta/<int:pk>/preview/', ComercialProposalPreview, name='proposal_detail')
]