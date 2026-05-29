import pytest
from django.contrib.auth import get_user_model

from ..services import GroupService
from ..models import (
    GroupMember,
    PayingQueueGroup
)
from ..exceptions import (
    NotCurrentPayer,
    MemberNotInGroup
)

User = get_user_model()


# ---------------- ADVANCE ----------------


@pytest.mark.django_db
def test_advance_paying_wraparound():
    u1 = User.objects.create_user("u1")
    u2 = User.objects.create_user("u2")

    group = GroupService.create_group(owner=u1, name="test")

    m1 = GroupMember.objects.get(group=group, user=u1)
    m2 = GroupService.join_group(group=group, user=u2).member

    GroupService.advance_paying_member(group, acting_member=m1)
    result = GroupService.advance_paying_member(group, acting_member=m2)

    assert result.new_payer_id == m1.id


@pytest.mark.django_db
def test_advance_wrong_actor():
    u1 = User.objects.create_user("u1")
    u2 = User.objects.create_user("u2")

    group = GroupService.create_group(owner=u1, name="test")

    m2 = GroupService.join_group(group=group, user=u2).member

    with pytest.raises(NotCurrentPayer):
        GroupService.advance_paying_member(group=group, acting_member=m2)


# ---------------- SET ----------------


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


# ---------------- JOIN ----------------


@pytest.mark.django_db
def test_join_is_idempotent():
    u1 = User.objects.create_user("u1")
    u2 = User.objects.create_user("u2")

    group = GroupService.create_group(owner=u1, name="test")

    r1 = GroupService.join_group(group, u2)
    r2 = GroupService.join_group(group, u2)

    assert r1.created is True
    assert r2.created is False
    assert r1.member.id == r2.member.id
    assert GroupMember.objects.filter(group=group, user=u2).count() == 1



@pytest.mark.django_db
def test_join_order_increment():
   u1 = User.objects.create_user("u1")
   u2 = User.objects.create_user("u2")
   u3 = User.objects.create_user("u3")

   group = GroupService.create_group(owner=u1, name="test")

   GroupService.join_group(group, u2)
   m3 = GroupService.join_group(group, u3).member


   assert m3.order == 3


# ---------------- LEAVE ----------------


@pytest.mark.django_db
def test_leave_order_normalized():
   u1 = User.objects.create_user("u1")
   u2 = User.objects.create_user("u2")
   u3 = User.objects.create_user("u3")

   group = GroupService.create_group(owner=u1, name="test")
   m1 = GroupMember.objects.get(group=group, user=u1)
   GroupService.join_group(group, u2)
   GroupService.join_group(group, u3)

   GroupService.leave_group(group, m1)

   orders = list(group.members.order_by("order").values_list("order", flat=True))
   assert orders == list(range(1, len(orders) + 1))


@pytest.mark.django_db
def test_leave_last_member_deletes_group():
   u1 = User.objects.create_user("u1")

   group = GroupService.create_group(owner=u1, name="test")
   m1 = GroupMember.objects.get(group=group, user=u1)

   result = GroupService.leave_group(group, m1)

   assert result.group_deleted is True
   assert not PayingQueueGroup.objects.filter(id=group.id).exists()


@pytest.mark.django_db
def test_leave_auto_advance_payer():
    u1 = User.objects.create_user("u1")
    u2 = User.objects.create_user("u2")

    group = GroupService.create_group(owner=u1, name="test")
    m1 = GroupMember.objects.get(group=group, user=u1)
    m2 = GroupService.join_group(group, u2).member

    result = GroupService.leave_group(group, m1)

    assert result.current_payer_id == m2.id
