from django.db import transaction, IntegrityError
from .models import PayingQueueGroup, GroupMember, PayingState
from .utils import generate_group_code
from .exceptions import (
    GroupCodeGenerationError,
    GroupClosed,
    MemberNotInGroup,
    NotCurrentPayer,
)
from dataclasses import dataclass
from django.db.models import Max
from django.core.exceptions import ValidationError


@dataclass(frozen=True)
class JoinGroupResult:
    member: GroupMember
    created: bool


@dataclass(frozen=True)
class LeaveGroupResult:
    group_deleted: bool
    current_payer_id: int | None
    owner_member_id: int | None


@dataclass(frozen=True)
class AdvancePayerResult:
    new_payer_id: int


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

        current_payer_id = PayingState.objects.get(group=group).current_paying_member_id
        if current_payer_id == member.id:
            current_payer_id = GroupService.advance_paying_member(
                group=group,
                acting_member=member,
            ).new_payer_id

        member.delete()

        GroupService.normalize_member_order(group)
        if group.owner == member.user:
            group.owner = remaining_members[0].user
            group.save(update_fields=["owner"])

        owner_member_id = group.members.get(user=group.owner).id

        return LeaveGroupResult(
            group_deleted=False,
            current_payer_id=current_payer_id,
            owner_member_id=owner_member_id,
        )

    @staticmethod
    def normalize_member_order(group):
        members = list(group.members.order_by("order"))

        for index, member in enumerate(members, start=1):
            if member.order != index:
                member.order = index
                member.save(update_fields=["order"])

    @staticmethod
    @transaction.atomic
    def advance_paying_member(group, acting_member):
        try:
            group = (
                PayingQueueGroup.objects
                .select_for_update()
                .get(id=group.id)
            )
        except PayingQueueGroup.DoesNotExist:
            raise GroupClosed(
                "Cannot advance turn: group was closed."
            )

        current_payer = group.paying_state.current_paying_member
        if acting_member != current_payer:
            raise NotCurrentPayer("Cannot advance turn: acting member is not a current payer.")

        members = list(group.members.order_by("order"))
        current_index = members.index(current_payer)
        next_index = (current_index + 1) % len(members)
        new_payer = members[next_index]

        group.paying_state.current_paying_member = new_payer
        group.paying_state.save(update_fields=["current_paying_member"])

        return AdvancePayerResult(
            new_payer_id=new_payer.id
        )

    @staticmethod
    @transaction.atomic
    def reorder_members(group, new_order):
        members = list(group.members.all())

        member_ids = {m.id for m in members}
        new_order_set = set(new_order)

        if new_order_set != member_ids:
            raise ValidationError(
                "new_order must contain exactly all group members"
            )

        order_map = {member_id: index for index, member_id in enumerate(new_order, start=1)}

        for i, member in enumerate(members):
            member.order = i + 1000

        GroupMember.objects.bulk_update(members, ["order"])

        for member in members:
            member.order = order_map[member.id]

        GroupMember.objects.bulk_update(members, ["order"])


    @staticmethod
    @transaction.atomic
    def set_current_payer(group, member):
        group = (
            PayingQueueGroup.objects
            .select_for_update()
            .get(id=group.id)
        )
        try:
            member = group.members.get(id=member.id)
        except GroupMember.DoesNotExist:
            raise MemberNotInGroup("Cannot set payer: this member is not in group.")

        group.paying_state.current_paying_member = member
        group.paying_state.save()
