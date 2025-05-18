from django.urls import path, re_path
from . import consumers

websocket_urlpatterns = [
    path('ws/delivery/notifications/', consumers.DeliveryConsumer.as_asgi()),
    path('ws/server/notifications/',   consumers.ServerConsumer.as_asgi()),
]
print("🛰️ websocket_urlpatterns:", websocket_urlpatterns)