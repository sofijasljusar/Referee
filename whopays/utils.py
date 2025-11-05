from .models import GroupMember


def normalize_order(group):
    for index, member in enumerate(group.members.all(), start=1):
        if member.order != index:
            member.order = index
    GroupMember.objects.bulk_update(group.members.all(), ["order"])
