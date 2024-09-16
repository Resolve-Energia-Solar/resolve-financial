from django.urls import include, path
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('users', UserViewSet)

app_name = 'api'
urlpatterns = [
    path('', include(router.urls)),
]
