import regex
from django.core.exceptions import ValidationError


def normalize_order(group):
    from .models import GroupMember
    members = group.members.all()
    for index, member in enumerate(members, start=1):
        if member.order != index:
            member.order = index
    GroupMember.objects.bulk_update(members, ["order"])


def validate_single_emoji(value):
    if len(regex.findall(r'\X', value)) != 1:
        raise ValidationError("Please enter exactly one emoji.")


def pass_ownership(group):
    remaining_members = list(group.members.all())

    if not remaining_members:
        group.delete()
        return

    group.owner = remaining_members[0].user
    group.save()
