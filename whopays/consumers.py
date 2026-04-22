import json
from channels.generic.websocket import AsyncWebsocketConsumer


class GroupConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.code = self.scope["url_route"]["kwargs"]["code"]
        self.group_name = f"group_{self.code}"

        await  self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def payer_changed(self, event):
        await self.send(text_data=json.dumps({
            "type": "payer_changed",
            "current_payer": event["current_payer"]
        }))

