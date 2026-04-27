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
            "current_payer_id": event["current_payer_id"],
        }))

    async def queue_reordered(self, event):
        await self.send(text_data=json.dumps({
            "type": "queue_reordered",
            "new_order": event["new_order"],
        }))

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_joined",
            "new_member_id": event["new_member_id"],
            "new_member_username": event["new_member_username"],
        }))
