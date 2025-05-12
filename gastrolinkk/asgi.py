import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import orders.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gastrolinkk.settings')

print("🚀 Loaded websocket_urlpatterns:", orders.routing.websocket_urlpatterns)

django_asgi = get_asgi_application()
application = ProtocolTypeRouter({
    "http": django_asgi,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            orders.routing.websocket_urlpatterns
        )
    ),
})