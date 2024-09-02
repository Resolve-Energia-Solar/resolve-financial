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
    
    # Marketing Campaign
    path('campanhas/', MarketingCampaignListView.as_view(), name='campaign_list'),
    path('campanhas/<int:pk>/', MarketingCampaignDetailView.as_view(), name='campaign_detail'),
    path('campanhas/criar/', MarketingCampaignCreateView.as_view(), name='campaign_create'),
    path('campanhas/<int:pk>/editar/', MarketingCampaignUpdateView.as_view(), name='campaign_update'),

    # ComercialProposal
    # path('proposta/<int:pk>/', ComercialProposalDetailView.as_view(), name='proposal_detail'),
    # path('proposta/<int:pk>/preview/', ComercialProposalPreview, name='proposal_detail')
]