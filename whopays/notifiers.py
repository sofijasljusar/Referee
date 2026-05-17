from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class GroupRealtimeNotifier:

    @staticmethod
    def member_left(code, member_id, result):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"group_{code}",
            {
                "type": "member_left",
                "member_id": member_id,
                "group_deleted": result.group_deleted,
                "current_payer_id": result.current_payer_id,
                "owner_member_id": result.owner_member_id,
            }
        )

    @staticmethod
    def user_joined(code, new_member):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"group_{code}",
            {
                "type": "user_joined",
                "new_member_id": new_member.id,
                "new_member_username": new_member.user.username,
            }
        )

