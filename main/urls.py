from django.urls import path

from .views import *

app_name = 'main'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('quadro/<int:pk>', KanbanView.as_view(), name='board-detail'),
]