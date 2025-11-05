from .models import GroupMember


def normalize_order(group):
    members = group.members.all()
    for index, member in enumerate(members, start=1):
        if member.order != index:
            member.order = index
    GroupMember.objects.bulk_update(members, ["order"])