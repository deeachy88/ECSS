from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path(
        'ws/socketserver/<str:thread_id>/',
        consumers.IdConsumer.as_asgi()
    ),
]