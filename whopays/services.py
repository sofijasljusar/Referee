from django.db import transaction, IntegrityError
from .models import PayingQueueGroup, GroupMember, PayingState
from .utils import generate_group_code
from .exceptions import EmptyGroupError, InvalidPayingStateError, GroupCodeGenerationError, GroupClosed
from dataclasses import dataclass
from django.db.models import Max


@dataclass(frozen=True)
class JoinGroupResult:
    member: GroupMember
    created: bool


@dataclass(frozen=True)
class LeaveGroupResult:
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
                    return GroupService._create_group_with_code_and_initial_state(owner, data)
            except IntegrityError:
                continue
        else:
            raise GroupCodeGenerationError()

    @staticmethod
    def _create_group_with_code_and_initial_state(owner, data):
        group = PayingQueueGroup.objects.create(
            code=generate_group_code(PayingQueueGroup.CODE_LENGTH),
            **data
        )

        result = GroupService.join_group(
            group=group,
            user=owner,
        )
        member = result.member

        PayingState.objects.create(
            group=group,
            current_paying_member=member,
        )
        return group

    @staticmethod
    @transaction.atomic
    def close_group(group):
        group = (
            PayingQueueGroup.objects
            .select_for_update()
            .get(id=group.id)
        )
        group.paying_state.delete()
        group.delete()

    @staticmethod
    @transaction.atomic
    def join_group(group, user):
        try:
            group = (
                PayingQueueGroup.objects
                .select_for_update()
                .get(id=group.id)
            )
        except PayingQueueGroup.DoesNotExist:
            raise GroupClosed(
                "Cannot join group: group was closed."
            )

        last_order = (
            group.members.aggregate(Max("order"))["order__max"]
            or 0
        )

        member, created = GroupMember.objects.get_or_create(
            group=group,
            user=user,
            defaults={"order": last_order + 1},
        )

        return JoinGroupResult(
            member=member,
            created=created
        )

    @staticmethod
    @transaction.atomic
    def leave_group(group, member):
        try:
            group = (
                PayingQueueGroup.objects
                .select_for_update()
                .get(id=group.id)
            )
        except PayingQueueGroup.DoesNotExist:
            raise GroupClosed(
                "Cannot leave group: group was closed."
            )

        remaining_members = list(group.members.exclude(id=member.id))

        if not remaining_members:
            GroupService.close_group(group)
            return LeaveGroupResult(
                group_deleted=True,
                current_payer_id=None,
                owner_member_id=None,
            )

        paying_state = group.paying_state
        if paying_state.current_paying_member_id == member.id:
            GroupService.advance_paying_member(group)

        member.delete()

        GroupService.normalize_member_order(group)
        if group.owner == member.user:
            group.owner = remaining_members[0].user
            group.save(update_fields=["owner"])

        owner_member_id = group.members.get(user=group.owner).id

        return LeaveGroupResult(
            group_deleted=False,
            current_payer_id=paying_state.current_paying_member_id,
            owner_member_id=owner_member_id,
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
    def advance_paying_member(group):
        members = list(group.members.order_by("order"))
        if not members:
            raise EmptyGroupError(
                "Cannot advance turn: group has no members."
            )

        current = group.paying_state.current_paying_member
        try:
            current_index = members.index(current)
        except ValueError:
            raise InvalidPayingStateError(
                "Cannot advance turn: current payer is not a member of this group."
            )

        next_index = (current_index + 1) % len(members)
        group.paying_state.current_paying_member = members[next_index]
        group.paying_state.save(update_fields=["current_paying_member"])

    @staticmethod
    @transaction.atomic
    def reorder_members(group, new_order):
        members = list(group.members.all())
        order_map = {member_id: index for index, member_id in enumerate(new_order, start=1)}

        for i, member in enumerate(members):
            member.order = i + 1000

        GroupMember.objects.bulk_update(members, ["order"])

        for member in members:
            member.order = order_map[member.id]

        GroupMember.objects.bulk_update(members, ["order"])


    @staticmethod
    def set_current_payer(group, member):
        group.paying_state.current_paying_member = member
        group.paying_state.save()
