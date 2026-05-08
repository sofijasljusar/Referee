from django.db import transaction, IntegrityError
from .models import PayingQueueGroup, GroupMember, PayingState
from .utils import generate_group_code
from .exceptions import EmptyGroupError, InvalidPayingStateError, GroupCodeGenerationError
from dataclasses import dataclass
from django.db.models import Max


@dataclass
class RemoveMemberResult:
    group_deleted: bool
    current_payer_id: int | None
    owner_member_id: int | None


class GroupService:

    @staticmethod
    def create_group(owner, name, emoji=None):
        data = {
            "owner": owner,
            "name": name,
        }
        if emoji is not None:
            data["emoji"] = emoji

        for _ in range(3):
            try:
                with transaction.atomic():
                    group = PayingQueueGroup.objects.create(
                        code=generate_group_code(PayingQueueGroup.CODE_LENGTH),
                        **data
                    )

                    member = GroupService.add_member(
                        group=group,
                        user=owner,
                    )

                    PayingState.objects.create(
                        group=group,
                        current_paying_member=member,
                    )
                    return group
            except IntegrityError:
                continue
        else:
            raise GroupCodeGenerationError()

    @staticmethod
    def add_member(group, user):
        last_order = (
            group.members.aggregate(Max("order"))["order__max"]
            or 0
        )

        return GroupMember.objects.get_or_create(
            group=group,
            user=user,
            defaults={"order": last_order + 1},
        )

    @staticmethod
    def normalize_member_order(group):
        members = list(group.members.order_by("order"))
        to_update = []

        for index, member in enumerate(members, start=1):
            if member.order != index:
                member.order = index
                to_update.append(member)

        GroupMember.objects.bulk_update(to_update, ["order"])

    @staticmethod
    @transaction.atomic
    def remove_member(group, member):
        is_owner = (group.owner == member.user)

        remaining_members = list(group.members.exclude(id=member.id))
        if not remaining_members:
            GroupService.close_group(group)
            return RemoveMemberResult(
                group_deleted=True,
                current_payer_id=None,
                owner_member_id=None,
            )

        paying_state = group.paying_state
        if paying_state.current_paying_member_id == member.id:
            GroupService.advance_paying_member(group)

        member.delete()

        GroupService.normalize_member_order(group)
        if is_owner:
            group.owner = remaining_members[0].user
            group.save(update_fields=["owner"])
        owner_member_id = group.members.get(user=group.owner).id

        return RemoveMemberResult(
            group_deleted=False,
            current_payer_id=paying_state.current_paying_member_id,
            owner_member_id=owner_member_id,
        )

    @staticmethod
    @transaction.atomic
    def close_group(group):
        group.paying_state.delete()
        group.delete()

    @staticmethod
    def advance_paying_member(group):
        members = list(group.members.order_by("order"))
        member_ids = [m.id for m in members]

        if not members:
            raise EmptyGroupError(
                "Cannot advance turn: group has no members."
            )

        current = group.paying_state.current_paying_member
        if current.id not in member_ids:
            raise InvalidPayingStateError(
                "Cannot advance turn: current payer is not a member of this group."
            )

        current_index = members.index(current)
        next_index = (current_index + 1) % len(members)
        group.paying_state.current_paying_member = members[next_index]
        group.paying_state.save(update_fields=["current_paying_member"])



