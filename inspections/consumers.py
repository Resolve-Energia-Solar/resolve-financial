import json
from asgiref.sync import sync_to_async, async_to_sync
from channels.layers import get_channel_layer
from channels.generic.websocket import AsyncWebsocketConsumer


class LocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.group_name = None 

        if not self.user.is_authenticated:
            await self.close()
            return
        
        is_supervisor = await sync_to_async(
            self.user.user_permissions.filter(codename="view_agentroute").exists
        )()

        is_client = await sync_to_async(
            self.user.user_types.filter(name="Cliente").exists
        )()

        is_agent = await sync_to_async(
            self.user.user_types.filter(name="agent").exists
        )()

        if is_supervisor:
            self.group_name = "supervisors"
        elif is_client:
            self.group_name = f"client_{self.user.id}"
        elif is_agent:
            self.group_name = f"agent_{self.user.id}"

        if self.group_name:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            print(f"Usuário {self.user.username} conectado ao grupo {self.group_name}")
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            print(f"Usuário desconectado do grupo {self.group_name}")
        else:
            print("Erro: Nenhum grupo definido para este WebSocket")

    async def location_update(self, event):
        data = event["data"]
        await self.send(text_data=json.dumps(data))

    @staticmethod
    def send_location_update(update_data, *groups):
        channel_layer = get_channel_layer()
        for group in groups:
            async_to_sync(channel_layer.group_send)(
                group,
                {
                    "type": "location_update",
                    "data": update_data
                }
            )
