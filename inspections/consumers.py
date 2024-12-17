import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.generic.websocket import AsyncWebsocketConsumer


class LocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Conecta o WebSocket ao grupo correto com base no papel do usuário.
        """
        self.user = self.scope['user']
        self.group_name = None  # Inicializa self.group_name para evitar erros

        # Verifica se o usuário está autenticado
        if not self.user.is_authenticated:
            await self.close()
            return

        # Determina o grupo baseado no papel do usuário
        if self.user.is_staff:  # Supervisores
            self.group_name = "supervisors"
        elif self.user.groups.filter(name="Clientes").exists():  # Clientes
            self.group_name = f"client_{self.user.id}"
        else:  # Agentes de campo
            self.group_name = f"agent_{self.user.id}"

        # Adiciona o WebSocket ao grupo correto
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f"Usuário {self.user.username} conectado ao grupo {self.group_name}")

    async def disconnect(self, close_code):
        """
        Remove o WebSocket do grupo quando desconectado.
        """
        if self.group_name:  # Verifica se self.group_name foi definido
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            print(f"Usuário desconectado do grupo {self.group_name}")
        else:
            print("Erro: Nenhum grupo definido para este WebSocket")

    @staticmethod
    def send_location_update(data, supervisor_group="supervisors", client_group=None):
        """
        Método estático para enviar atualizações de localização para grupos específicos.
        """
        channel_layer = get_channel_layer()

        # Envia para o grupo de supervisores
        async_to_sync(channel_layer.group_send)(
            supervisor_group,
            {
                "type": "send_location_update",
                "message": data,
            },
        )

        # Se um grupo de cliente for especificado, envia também para o cliente
        if client_group:
            async_to_sync(channel_layer.group_send)(
                client_group,
                {
                    "type": "send_location_update",
                    "message": data,
                },
            )

    async def send_location_update(self, event):
        """
        Envia as atualizações de localização para os WebSockets conectados.
        """
        await self.send(text_data=json.dumps(event["message"]))
