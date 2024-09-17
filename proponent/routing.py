from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/socketserver/', consumers.IdConsumer.as_asgi()),
]
