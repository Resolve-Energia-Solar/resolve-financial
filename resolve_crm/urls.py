from django.urls import path

from .views import *

app_name = 'resolve_crm'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    # Boards
    path('quadro/<int:pk>', KanbanView.as_view(), name='board-detail'),
    path('quadros/', BoardsView.as_view(), name='boards'),
    path('quadros/criar', BoardCreateView.as_view(), name='board-create'),
    path('quadros/<int:pk>/editar/', BoardUpdateView.as_view(), name='board-update'),
    path('quadros/<int:pk>/<int:column_id>/criar', CreateCardView.as_view(), name='card-create'),
    # Tasks
    path('tarefas/', TasksView.as_view(), name='tasks'),
    path('tarefas/<int:pk>', TaskDetailView.as_view(), name='task-detail'),
    path('tarefas/criar', TaskCreateView.as_view(), name='task-create'),
    path('tarefas/<int:pk>/editar/', TaskUpdateView.as_view(), name='task-update'),
    path('move_card/<int:table_id>/<int:column_id>/<int:card_id>', MoveCardView.as_view(), name='move_card'),
    path('coluna/<int:column_id>/deletar', DeleteColumnView.as_view(), name='column-delete'),
    # Leads
    path('leads/criar', LeadCreateView.as_view(), name='lead_create'),
    path('leads/', LeadListView.as_view(), name='lead_list'),
    path('leads/<int:pk>/', LeadDetailView.as_view(), name='lead_detail'),
    path('leads/<int:pk>/editar', LeadUpdateView.as_view(), name='lead_update'),
]