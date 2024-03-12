from django.urls import path

from .views import *

app_name = 'main'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('quadro/<int:pk>', KanbanView.as_view(), name='board-detail'),
    path('tarefas/', TasksView.as_view(), name='tasks'),
    path('tarefas/<int:pk>', TaskDetailView.as_view(), name='task-detail'),
    path('tarefas/criar', TaskCreateView.as_view(), name='task-create'),
    path('tarefas/<int:pk>/editar', TaskUpdateView.as_view(), name='task-update')
]