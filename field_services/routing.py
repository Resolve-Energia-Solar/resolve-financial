from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/location/', consumers.LocationConsumer.as_asgi()),
]