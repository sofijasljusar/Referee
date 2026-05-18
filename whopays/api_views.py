from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import PayingQueueGroup, GroupMember, UserProfile
from .services import GroupService
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .serializers import ThemeColorSerializer


class UpdateThemeColorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ThemeColorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.theme_color = serializer.validated_data["theme_color"]
        profile.save(update_fields=["theme_color"])

        return Response({"status": "ok"})



class ReorderQueueAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, code):
        group = PayingQueueGroup.objects.get(code=code)
        if group.owner != request.user:
            return Response({"status": "error", "message": "Only owner can reorder queue."}, status=403)
        new_order = request.data.get("new_order", [])
        new_order = [int(i) for i in new_order]
        members = group.members.all()
        order_map = {member_id: index for index, member_id in enumerate(new_order, start=1)}

        for i, member in enumerate(members):
            member.order = i + 1000

        GroupMember.objects.bulk_update(members, ["order"])

        for member in members:
            member.order = order_map[member.id]

        GroupMember.objects.bulk_update(members, ["order"])

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"group_{code}",
            {
                "type": "queue_reordered",
                "new_order": new_order,
            }
        )

        return Response({"status": "success"})


class SetCurrentPayingMember(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, code):
        group = PayingQueueGroup.objects.get(code=code)
        if group.owner != request.user:
            return Response({"status": "error", "message": "Only owner can set current payer."}, status=403)

        member = group.members.get(id=request.data.get("member_id"))
        group.paying_state.current_paying_member = member
        group.paying_state.save()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"group_{code}",
            {
                "type": "payer_changed",
                "current_payer_id": member.id,
            }
        )

        return Response({"status": "success",  "current_payer": member.user.username})


class AdvanceTurnAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, code):
        group = PayingQueueGroup.objects.get(code=code)
        current_paying_member = group.paying_state.current_paying_member

        if current_paying_member.user != request.user:
            return Response({"status": "error", "message": "Only current paying member can advance turn."}, status=403)

        GroupService.advance_paying_member(group)
        new_current = group.paying_state.current_paying_member

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"group_{code}",
            {
                "type": "payer_changed",
                "current_payer_id": new_current.id,
            }
        )

        return Response({
            "status": "success",
            "current_payer_id": new_current.id,
        })
