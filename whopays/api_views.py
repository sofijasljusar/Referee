from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import PayingQueueGroup, UserProfile
from .services import GroupService
from .serializers import ThemeColorSerializer, ReorderMembersSerializer, SetCurrentPayerSerializer
from rest_framework import status
from django.shortcuts import get_object_or_404
from .notifiers import GroupRealtimeNotifier
from .exceptions import GroupClosed, MemberLeft


class UpdateThemeColorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ThemeColorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.theme_color = serializer.validated_data["theme_color"]
        profile.save(update_fields=["theme_color"])

        return Response(status=status.HTTP_204_NO_CONTENT)



class ReorderQueueAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, code):
        group = get_object_or_404(PayingQueueGroup, code=code)

        if group.owner != request.user:
            return Response(
                {"detail": "Only owner can reorder queue."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = ReorderMembersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_order = serializer.validated_data["new_order"]

        GroupService.reorder_members(
            group=group,
            new_order=new_order,
        )

        GroupRealtimeNotifier.queue_reordered(
            code=code,
            new_order=new_order,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class SetCurrentPayingMember(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, code):
        group = get_object_or_404(PayingQueueGroup, code=code)

        if group.owner != request.user:
            return Response(
                {"detail": "Only owner can set current payer."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = SetCurrentPayerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member_id = serializer.validated_data["member_id"]
        member = get_object_or_404(
            group.members,
            id=member_id,
        )
        try:
            GroupService.set_current_payer(
                group=group,
                member=member,
            )
        except MemberLeft as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT
            )

        GroupRealtimeNotifier.payer_changed(
            code=code,
            member_id=member_id,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class AdvanceTurnAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, code):
        group = get_object_or_404(PayingQueueGroup, code=code)
        current_paying_member = group.paying_state.current_paying_member

        if current_paying_member.user != request.user:
            return Response(
                {"detail": "Only current paying member can advance turn."},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            GroupService.advance_paying_member(group)
        except GroupClosed as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT
            )

        new_current = group.paying_state.current_paying_member

        GroupRealtimeNotifier.payer_changed(
            code=code,
            member_id=new_current.id,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
