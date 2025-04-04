from api.urls import router
from core.views import *
from django.urls import path


router.register('lead-tasks', TaskViewSet, basename='lead-task')
router.register('attachments', AttachmentViewSet, basename='attachment')
router.register('comments', CommentViewSet, basename='comment')
router.register('content-types', ContentTypeViewSet, basename='content-type')
router.register('tasks', TaskViewSet, basename='task')
router.register('task-templates', TaskTemplatesViewSet, basename='task-template')
router.register('boards', BoardViewSet, basename='board')
router.register('columns', ColumnViewSet, basename='column')
router.register('document-types', DocumentTypeViewSet, basename='document-type')
router.register('document-subtypes', DocumentSubTypeViewSet, basename='document-subtype')
router.register('notifications', NotificationViewSet, basename='notification')
router.register('tags', TagViewSet, basename='tag')

urlpatterns = [
    path('processos/<int:pk>/', ProcessDetailView.as_view(), name='detalhe-processo'),
    path('processos/<int:process_id>/etapas/<int:etapa_id>/concluir/', ConcluirEtapaView.as_view(), name='concluir-etapa'),
    path('processos/por-objeto/<str:app_label>/<str:model>/<int:object_id>/', ProcessByObjectView.as_view(), name='processo-por-objeto'),
]