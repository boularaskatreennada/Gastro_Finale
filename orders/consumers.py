import json
from channels.layers import get_channel_layer
from channels.generic.websocket import AsyncWebsocketConsumer
class DeliveryConsumer(AsyncWebsocketConsumer):
    group_name = "delivery_group"

    async def connect(self):
        print("⚡ WebSocket connection received!")  # Debug line
        
        # join the group
        await self.channel_layer.group_add(
            
            self.group_name,
            self.channel_name
        )
        await self.accept()
       

    async def disconnect(self, close_code):
        # leave the group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": "notification",
            "data": event["data"]  # Properly nest data
        }))