import json
import logging

from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async


logger = logging.getLogger(__name__)


class LocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.group_name = None

        if not self.user.is_authenticated:
            await self.close()
            return

        is_supervisor = await sync_to_async(
            self.user.user_permissions.filter(codename="change_schedule").exists
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
            logger.info(
                f"Usuário {self.user.username} conectado ao grupo {self.group_name}"
            )
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            logger.info(f"Usuário desconectado do grupo {self.group_name}")
        else:
            logger.error("Erro: Nenhum grupo definido para este WebSocket")

    async def location_update(self, event):
        data = event["data"]
        await self.send(text_data=json.dumps(data))

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"error": "Invalid data format"}))
            return

        # enviar para o cliente e para os supervisores
        customer_id = data.get("custumer_id")

        if customer_id:
            await self.channel_layer.group_send(
                f"client_{customer_id}", {"type": "location_update", "data": data}
            )

        await self.channel_layer.group_send(
            "supervisors", {"type": "location_update", "data": data}
        )

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            logger.info(f"Usuário desconectado do grupo {self.group_name}")
        else:
            logger.error("Erro: Nenhum grupo definido para este WebSocket")
        raise StopConsumer()
