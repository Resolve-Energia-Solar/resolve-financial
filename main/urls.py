from django.urls import path

from .views import *

app_name = 'main'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('quadro/<int:pk>', KanbanView.as_view(), name='board-detail'),
    path('tarefas/', TasksView.as_view(), name='tasks'),
    path('tarefas/<int:pk>', TaskDetailView.as_view(), name='task-detail'),
    path('tarefas/criar', TaskCreateView.as_view(), name='task-create'),
    path('tarefas/<int:pk>/editar', TaskUpdateView.as_view(), name='task-update'),
    path('quadros/', BoardsView.as_view(), name='boards'),
    path('quadros/criar', BoardCreateView.as_view(), name='board-create'),  
    path('move_card/<int:table_id>/<int:column_id>/<int:card_id>', MoveCardView.as_view(), name='move_card'),
    path('quadros/<int:pk>/<int:column_id>/criar', CreateCardView.as_view(), name='card-create'),
]