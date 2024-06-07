"""
ASGI config for ECS project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import proponent.routing
from channels.routing import URLRouter, ProtocolTypeRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ECS.settings')

#application = get_asgi_application()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            proponent.routing.websocket_urlpatterns
                ),
    )
})
