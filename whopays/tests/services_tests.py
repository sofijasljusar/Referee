import pytest
from django.contrib.auth import get_user_model

from whopays.services import GroupService
from whopays.models import GroupMember
from whopays.exceptions import (
    NotCurrentPayer,
    MemberNotInGroup
)

User = get_user_model()


@pytest.mark.django_db
def test_advance_paying_wraparound():
    u1 = User.objects.create_user("u1")
    u2 = User.objects.create_user("u2")

    group = GroupService.create_group(owner=u1, name="test")

    m1 = GroupMember.objects.get(group=group, user=u1)
    m2 = GroupService.join_group(group=group, user=u2).member

    GroupService.advance_paying_member(group, acting_member=m1)
    GroupService.advance_paying_member(group, acting_member=m2)

    assert group.paying_state.current_paying_member == m1


@pytest.mark.django_db
def test_advance_wrong_actor():
    u1 = User.objects.create_user("u1")
    u2 = User.objects.create_user("u2")

    group = GroupService.create_group(owner=u1, name="test")

    m2 = GroupService.join_group(group=group, user=u2).member

    with pytest.raises(NotCurrentPayer):
        GroupService.advance_paying_member(group=group, acting_member=m2)


@pytest.mark.django_db
def test_set_invalid_member():
    u1 = User.objects.create_user("u1")
    u2 = User.objects.create_user("u2")

    group = GroupService.create_group(owner=u1, name="test")
    other_group = GroupService.create_group(owner=u1, name="test")

    other_group_member = GroupService.join_group(
        group=other_group,
        user=u2
    ).member

    with pytest.raises(MemberNotInGroup):
        GroupService.set_current_payer(
            group=group,
            member=other_group_member
        )
