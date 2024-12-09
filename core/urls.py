from api.urls import router
from core.views import *


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
