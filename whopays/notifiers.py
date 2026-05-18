from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class GroupRealtimeNotifier:

    @staticmethod
    def _send(code, event_type, payload):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"group_{code}",
            {
                "type": event_type,
                **payload,
            }
        )

    @staticmethod
    def user_joined(code, new_member):
        GroupRealtimeNotifier._send(
            code,
            "user_joined",
            {
                "new_member_id": new_member.id,
                "new_member_username": new_member.user.username,
            }
        )

    @staticmethod
    def member_left(code, member_id, result):
        GroupRealtimeNotifier._send(
            code,
            "member_left",
            {
                "member_id": member_id,
                "group_deleted": result.group_deleted,
                "current_payer_id": result.current_payer_id,
                "owner_member_id": result.owner_member_id,
            }
        )

    @staticmethod
    def payer_changed(code, member_id):
        GroupRealtimeNotifier._send(
            code,
            "payer_changed",
            {
                "current_payer_id": member_id,
            }
        )

    @staticmethod
    def queue_reordered(code, new_order):
        GroupRealtimeNotifier._send(
            code,
            "queue_reordered",
            {
                "new_order": new_order,
            }
        )