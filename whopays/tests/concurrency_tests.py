from django.contrib.auth.models import User
from ..services import GroupService
from ..models import GroupMember, PayingQueueGroup
from .utils import ConcurrentTestCase


class JoinRaceTest(ConcurrentTestCase):
    reset_sequences = True

    def setUp(self):
        self.user1 = User.objects.create_user("u1")
        self.user2 = User.objects.create_user("u2")
        self.user3 = User.objects.create_user("u3")
        self.group = GroupService.create_group(owner=self.user1, name="test")

    def test_concurrent_join_for_duplicated_order(self):
        def f1():
            GroupService.join_group(group=self.group, user=self.user2)
        def f2():
            GroupService.join_group(group=self.group, user=self.user3)

        errors = self.run_concurrently([f1, f2])
        self.assertFalse(errors)

        queue_orders = list(
            GroupMember.objects
            .filter(group=self.group)
            .values_list("order", flat=True)
        )
        self.assertEqual(len(queue_orders), len(set(queue_orders)))


class LeaveRaceTest(ConcurrentTestCase):
    reset_sequences = True

    def setUp(self):
        self.owner = User.objects.create_user("u1")
        self.user = User.objects.create_user("u2")
        self.group = GroupService.create_group(
            owner=self.owner,
            name="test"
        )
        self.member = GroupService.join_group(
            group=self.group,
            user=self.user
        ).member

    def test_concurrent_leave_for_stale_remaining(self):
        def f1():
            GroupService.leave_group(
                group=self.group,
                member=self.group.members.get(user=self.owner)
            )

        def f2():
            GroupService.leave_group(
                group=self.group,
                member=self.member
            )

        errors = self.run_concurrently([f1, f2])
        self.assertFalse(errors)
        self.assertFalse(GroupMember.objects.filter(group=self.group).exists())
        self.assertFalse(PayingQueueGroup.objects.filter(id=self.group.id).exists())

