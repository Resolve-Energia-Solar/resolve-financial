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
router.register('processes', ProcessViewSet, basename='process')
router.register('steps-names', StepNameViewSet, basename='step-name')
router.register('content-types-endpoints', ContentTypeEndpointViewSet, basename='content-type-endpoint')

urlpatterns = [
    path('process/<int:pk>/', ProcessDetailView.as_view(), name='detalhe-processo'),
    path('process/<int:process_id>/step/<int:id>/finish/', FinishStepView.as_view(), name='finish-step'),
    path('process/por-objeto/<str:app_label>/<str:model>/<int:object_id>/', ProcessByObjectView.as_view(), name='process-per-object'),
    path('process-count-by-step/', ProcessStepCountListView.as_view(), name='process-count-by-step'),
]