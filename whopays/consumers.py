from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async


@database_sync_to_async
def user_in_group(user, code):
    from whopays.models import GroupMember

    return GroupMember.objects.filter(
        group__code=code,
        user=user
    ).exists()


class GroupConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.code = self.scope["url_route"]["kwargs"]["code"]
        self.group_name = f"group_{self.code}"

        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        allowed = await user_in_group(user, self.code)

        if not allowed:
            await self.close()
            return

        await self.channel_layer.group_add(
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
        await self.send_json({
            "type": "payer_changed",
            "current_payer_id": event["current_payer_id"],
        })

    async def queue_reordered(self, event):
        await self.send_json({
            "type": "queue_reordered",
            "new_order": event["new_order"],
        })

    async def user_joined(self, event):
        await self.send_json({
            "type": "user_joined",
            "new_member_id": event["new_member_id"],
            "new_member_username": event["new_member_username"],
        })

    async def member_left(self, event):
        await self.send_json({
            "type": "member_left",
            "member_id": event["member_id"],
            "group_deleted": event["group_deleted"],
            "current_payer_id": event["current_payer_id"],
            "owner_member_id": event["owner_member_id"]
        })
