from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import PayingQueueGroup, GroupMember


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

        for member in members:
            member.order = order_map[member.id]

        GroupMember.objects.bulk_update(members, ["order"])

        return Response({"status": "success"})


class SetCurrentPayingMember(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, code):
        group = PayingQueueGroup.objects.get(code=code)
        if group.owner != request.user:
            return Response({"status": "error", "message": "Only owner can set current payer."}, status=403)

        member_id = request.data.get("member_id")
        member = group.members.get(id=member_id)
        group.paying_state.current_paying_member = member
        group.paying_state.save()

        return Response({"status": "success",  "current_payer": member.user.username})


class AdvanceTurnAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, code):
        group = PayingQueueGroup.objects.get(code=code)
        current_paying_member = group.paying_state.current_paying_member

        if current_paying_member.user != request.user:
            return Response({"status": "error", "message": "Only current paying member can advance turn."}, status=403)

        group.paying_state.advance_paying_member()
        new_current = group.paying_state.current_paying_member

        return Response({
            "status": "success",
            "current_payer": new_current.user.username
        })
