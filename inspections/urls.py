from api.urls import router
from inspections.views import *


router.register('roof-types', RoofTypeViewSet, basename='roof-type')
router.register('categories', CategoryViewSet, basename='category')
router.register('deadlines', DeadlineViewSet, basename='deadline')
router.register('services', ServiceViewSet, basename='service')
router.register('forms', FormsViewSet, basename='form')
router.register('answers', AnswerViewSet, basename='answer')
router.register('schedule', ScheduleViewSet, basename='schedule')
router.register('block-time-agent', BlockTimeAgentViewSet, basename='block-time-agent')
router.register('free-time-agent', FreeTimeAgentViewSet, basename='free-time-agent')
