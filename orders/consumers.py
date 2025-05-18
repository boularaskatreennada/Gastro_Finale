from django.shortcuts import get_object_or_404
from django.utils import timezone
import json
from channels.layers import get_channel_layer
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from orders.models import Delivery, DeliveryStatus
from restaurant.models import DeliveryPerson

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
         print("💬 Consumer.send_notification got", event)
         await self.send(text_data=json.dumps(event["data"]))

         
    async def receive(self, text_data):
        print("🔍 receive() got:", text_data)   # ← debug
        msg = json.loads(text_data)
        if msg.get('action') == 'accept_order':
            order_id = msg['order_id']
            user = self.scope['user']
            print(f"🔍 accept_order for {order_id}")  # ← debug
            # 1) Lookup DeliveryPerson for this user
        try:
            delivery_person = await database_sync_to_async(lambda: user.deliveryperson)()
        except DeliveryPerson.DoesNotExist:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "You are not registered as a delivery person."
            }))
            return
        try:
            delivery= await database_sync_to_async(
             lambda: Delivery.objects.get(order_id=order_id,))()
        except Delivery.DoesNotExist:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "no delivery found "
            }))
            return
    
        
        delivery.delivery_person = delivery_person
        delivery.status = DeliveryStatus.INPROGRESS
        delivery.delivery_date = timezone.now()
        await database_sync_to_async(delivery.save)()

        # 3) Broadcast the “claimed” event
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "order.claimed",
                "order_id": order_id,
                "by": user.username,
            }
        )

# orders notif

class ServerConsumer(AsyncWebsocketConsumer):
    

    async def connect(self):
        user = self.scope['user']

        # 2) check in a thread if they have a Server profile
        is_server = await database_sync_to_async(
            lambda u: hasattr(u, 'server')
        )(user)

        if not is_server:
            # reject non‐servers
            return await self.close()

        # 3) now store it for later
        self.user = user
        self.group_name = f"server_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        print(f"🛰️ ServerConsumer: {user.username} joined {self.group_name}")
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        # event["data"] will come from your chef view
        await self.send(text_data=json.dumps(event["data"]))
