from rest_framework.permissions import BasePermission
from .models import PayingQueueGroup


class IsGroupOwner(BasePermission):
    def has_permission(self, request, view):
        code = view.kwargs["code"]

        return PayingQueueGroup.objects.filter(
            code=code,
            owner=request.user
        ).exists()
