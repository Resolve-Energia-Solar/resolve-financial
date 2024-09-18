from django.urls import path
from .views import *

app_name = 'core'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    # Boards
    path('quadros/', BoardList.as_view(), name='board-list'),
    path('quadros/novo/', BoardCreateView.as_view(), name='board-create'),
    path('quadros/<int:pk>/admin/', BoardDetailView.as_view(), name='board-admin'),
    path('quadros/<int:pk>/', KanbanView.as_view(), name='board-kanban'),
    path('quadros/<int:pk>/editar/', BoardUpdateView.as_view(), name='board-update'),
    # path('quadros/api/<int:pk>/', board_api, name='board-api'),
    # Columns
    # path('quadros/crm/<int:pk>/<int:column_id>/criar', CreateCardView.as_view(), name='card-create'),
    # path('move_card/<int:table_id>/<int:column_id>/<int:card_id>', MoveCardView.as_view(), name='move_card'),
    # path('coluna/criar/', CreateColumnView.as_view(), name='column-create'),
    # path('coluna/<int:column_id>/atualizar/', UpdateColumnView.as_view(), name='column-update'),
    # path('coluna/<int:column_id>/deletar/', DeleteColumnView.as_view(), name='column-delete'),
]