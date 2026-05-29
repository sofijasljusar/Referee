import pytest
from django.contrib.auth import get_user_model
from ..models import PayingState, GroupMember
from ..services import GroupService

User = get_user_model()

@pytest.mark.django_db
def test_advance_payer_persists_to_db():
   u1 = User.objects.create_user("u1")
   u2 = User.objects.create_user("u2")

   group = GroupService.create_group(owner=u1, name="test")
   m1 = GroupMember.objects.get(group=group, user=u1)

   m2 = GroupService.join_group(group=group, user=u2).member

   GroupService.advance_paying_member(group, acting_member=m1)
   GroupService.advance_paying_member(group, acting_member=m2)

   state = PayingState.objects.get(group=group)
   assert state.current_paying_member == m1

@pytest.mark.django_db
def test_set_payer_persists_to_db():
   u1 = User.objects.create_user("u1")
   u2 = User.objects.create_user("u2")

   group = GroupService.create_group(owner=u1, name="test")
   m2 = GroupService.join_group(group, u2).member

   GroupService.set_current_payer(group, m2)

   state = PayingState.objects.get(group=group)
   assert state.current_paying_member == m2
