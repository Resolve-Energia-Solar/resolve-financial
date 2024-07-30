from django.urls import path
from .views import *

app_name = 'core'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    # Boards
    path('quadros/', BoardList.as_view(), name='board-list'),
    path('quadros/novo/', BoardCreateView.as_view(), name='board-create'),
    path('quadros/<int:pk>/', KanbanView.as_view(), name='board-detail'),
    path('quadros/<int:pk>/editar/', BoardUpdateView.as_view(), name='board-update'),
    path('quadros/api/<int:pk>/', board_api, name='board-api'),
]