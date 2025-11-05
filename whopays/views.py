from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import PayingQueueGroup, GroupMember


class ReorderQueueAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, code):
        new_order = request.data.get("new_order", [])
        group = PayingQueueGroup.objects.get(code=code)
        members = group.members.all()
        order_map = {member_id: index for index, member_id in enumerate(new_order, start=1)}

        for member in members:
            member.order = order_map[member.id]

        GroupMember.objects.bulk_update(members, ["order"])

        return Response({"status": "success"})
